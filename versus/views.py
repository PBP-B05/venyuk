from __future__ import annotations

import json

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .forms import ChallengeCreateForm, CommunityForm
from .models import Challenge, Community, SportChoices


# ==========================
#  HELPERS (COMMUNITY & AUTH)
# ==========================

def _get_user_community(user) -> Community | None:
    """
    Community yang dimiliki user, atau yang di-join user.
    """
    if not user or not user.is_authenticated:
        return None

    owned = Community.objects.filter(owner=user).first()
    joined = Community.objects.filter(members=user).first()
    return owned or joined


def _ensure_user_community(request: HttpRequest):
    """
    Helper untuk WEB (HTML): user harus punya/join community dulu.
    """
    community = _get_user_community(request.user)
    if community is None:
        messages.info(
            request,
            "Kamu perlu membuat atau join community terlebih dahulu sebelum membuat atau join Versus.",
        )
        return None, redirect("versus:community_list")
    return community, None


def _get_request_data(request: HttpRequest) -> dict:
    """
    Support Flutter CookieRequest.post (form-data) dan JSON.
    """
    try:
        if request.content_type and "application/json" in request.content_type:
            raw = request.body.decode("utf-8") or "{}"
            return json.loads(raw)
    except Exception:
        pass
    return request.POST


def _resolve_user_from_request(request: HttpRequest):
    """
    1) Kalau request.user sudah authenticated => pakai itu
    2) Kalau cookie/session tidak kebawa => fallback dari body: user_id / username
    """
    if request.user.is_authenticated:
        return request.user

    data = _get_request_data(request)
    user_id = data.get("user_id")
    username = data.get("username")

    UserModel = get_user_model()

    if user_id:
        try:
            return UserModel.objects.get(pk=int(user_id))
        except Exception:
            return None

    if username:
        try:
            return UserModel.objects.get(username=username)
        except Exception:
            return None

    return None


def _json_get_user_or_401(request: HttpRequest):
    """
    Return (user, None) kalau dapat user, atau (None, JsonResponse 401) kalau tidak.
    """
    user = _resolve_user_from_request(request)
    if user:
        return user, None

    login_url = reverse("authenticate:login_api")  # sesuai app authenticate kamu
    return None, JsonResponse(
        {
            "ok": False,
            "status": "error",
            "requires_login": True,
            "login_url": login_url,
            "message": "Silakan login terlebih dahulu.",
        },
        status=401,
    )


def _can_manage_challenge(user, ch: Challenge) -> bool:
    """
    Hanya owner dari community host (yang membuat matchup) atau superuser.
    """
    if not user:
        return False
    return bool(user.is_superuser or (ch.host_id and ch.host.owner_id == user.id))


# ==========================
#  SERIALIZERS
# ==========================

def _serialize_community(comm: Community, user) -> dict:
    is_owner = bool(user and comm.owner_id == getattr(user, "id", None))
    is_member = bool(
        user and comm.members.filter(pk=getattr(user, "id", None)).exists()
    )

    return {
        "id": comm.pk,
        "name": comm.name,
        "primary_sport": comm.primary_sport,
        "primary_sport_label": comm.get_primary_sport_display(),
        "bio": comm.bio or "",
        "owner_username": comm.owner.username if comm.owner_id else "",
        # NOTE: owner biasanya sudah dimasukkan ke members => pakai count() aja (biar gak dobel)
        "total_members": comm.members.count(),
        "is_owner": is_owner,
        "is_member": is_member,
    }


def _serialize_challenge(ch: Challenge, user=None) -> dict:
    return {
        "id": ch.pk,
        "title": ch.title,
        "sport": ch.sport,
        "sport_label": ch.get_sport_display(),
        "match_category": ch.match_category,
        "match_category_label": ch.get_match_category_display(),
        "start_at": ch.start_at.isoformat() if ch.start_at else None,
        "status": ch.status,
        "status_label": ch.get_status_display(),
        "cost_per_person": ch.cost_per_person or 0,
        "prize_pool": ch.prize_pool or 0,
        "venue_name": ch.venue_name or "",
        "display_venue_name": ch.display_venue_name,
        "players_joined": ch.players_joined or 0,
        "max_players": ch.max_players,
        "detail_url": ch.get_absolute_url(),
        # Community info
        "host_id": ch.host_id,
        "host_name": ch.host.name if ch.host_id else "",
        "opponent_id": ch.opponent_id,
        "opponent_name": ch.opponent.name if ch.opponent_id else "",
        "has_opponent": ch.opponent_id is not None,
        "stage_community_size": ch.get_stage_community_size(),
        # tambahan mobile
        "description": ch.description or "",
        "poster_url": ch.banner_url or "",
        # ✅ permission flag untuk Flutter
        "can_manage": _can_manage_challenge(user, ch) if user else False,
    }


def _perform_join_for_community(ch: Challenge, community: Community):
    if ch.status != Challenge.Status.OPEN:
        return False, "Matchup sudah tidak open."

    cap = ch.get_stage_community_size() or 2

    if ch.players_joined >= cap:
        return False, "Slot community untuk matchup ini sudah penuh."

    if ch.host_id == community.id:
        return False, "Community kamu adalah host matchup ini."

    if ch.opponent_id == community.id:
        return False, "Community kamu sudah terdaftar sebagai opponent di matchup ini."

    if ch.opponent_id is None:
        ch.opponent = community

    ch.players_joined = (ch.players_joined or 0) + 1
    ch.save()
    ch.try_close()

    return True, f"Community kamu berhasil join. Total community: {ch.players_joined}/{cap}."


def _ensure_host_owner(request: HttpRequest, ch: Challenge) -> bool:
    u = request.user
    return bool(u.is_authenticated and (u.is_superuser or ch.host.owner_id == u.id))


# ==========================
#  WEB VERSUS PAGES (HTML)
# ==========================

def list_challenges(request: HttpRequest) -> HttpResponse:
    sport_q = (request.GET.get("sport") or "").strip().lower()

    qs = Challenge.objects.all().order_by("start_at")
    if sport_q:
        qs = qs.filter(sport=sport_q)

    return render(
        request,
        "versus/list.html",
        {
            "challenges": qs,
            "sports": SportChoices.choices,
            "sport_selected": sport_q,
        },
    )


def challenge_detail(request: HttpRequest, pk: int) -> HttpResponse:
    ch = get_object_or_404(Challenge, pk=pk)
    return render(request, "versus/detail.html", {"ch": ch})


@login_required(login_url="/authenticate/login/")
def create_challenge(request: HttpRequest) -> HttpResponse:
    community, redirect_resp = _ensure_user_community(request)
    if redirect_resp:
        return redirect_resp

    if request.method == "POST":
        form = ChallengeCreateForm(request.POST, community=community)
        if form.is_valid():
            ch = form.save_new()
            messages.success(request, "Matchup berhasil dibuat.")
            return redirect("versus:detail", ch.pk)
    else:
        form = ChallengeCreateForm(community=community)

    return render(
        request,
        "versus/create.html",
        {
            "form": form,
            "is_edit": False,
            "challenge": None,
        },
    )


@login_required(login_url="/authenticate/login/")
def update_challenge(request: HttpRequest, pk: int) -> HttpResponse:
    ch = get_object_or_404(Challenge, pk=pk)

    if not _ensure_host_owner(request, ch):
        messages.error(request, "Kamu tidak memiliki akses untuk mengedit matchup ini.")
        return redirect("versus:detail", pk=pk)

    if request.method == "POST":
        form = ChallengeCreateForm(request.POST, community=ch.host)
        if form.is_valid():
            form.apply_to_instance(ch)
            messages.success(request, "Matchup berhasil diupdate.")
            return redirect("versus:detail", pk=pk)
    else:
        initial = {
            "title": ch.title,
            "sport": ch.sport,
            "match_category": ch.match_category,
            "start_at": ch.start_at,
            "venue_name": ch.venue_name,
            "cost_per_person": ch.cost_per_person,
            "prize_pool": ch.prize_pool,
            "description": ch.description,
            "poster_url": ch.banner_url,
        }
        form = ChallengeCreateForm(initial=initial, community=ch.host)
        if "venue" in form.fields:
            form.initial["venue"] = ch.venue

    return render(
        request,
        "versus/create.html",
        {
            "form": form,
            "is_edit": True,
            "challenge": ch,
        },
    )


@login_required(login_url="/authenticate/login/")
def delete_challenge(request: HttpRequest, pk: int) -> HttpResponse:
    ch = get_object_or_404(Challenge, pk=pk)

    if not _ensure_host_owner(request, ch):
        messages.error(request, "Kamu tidak memiliki akses untuk menghapus matchup ini.")
        return redirect("versus:detail", pk=pk)

    if request.method == "POST":
        ch.delete()
        messages.success(request, "Matchup berhasil dihapus.")
        return redirect("versus:list")

    return render(request, "versus/confirm_delete.html", {"ch": ch})


@login_required(login_url="/authenticate/login/")
@require_POST
def join_challenge(request: HttpRequest, pk: int) -> HttpResponse:
    community, redirect_resp = _ensure_user_community(request)
    if redirect_resp:
        return redirect_resp

    ch = get_object_or_404(Challenge, pk=pk)

    ok, msg = _perform_join_for_community(ch, community)
    if ok:
        messages.success(request, msg)
    else:
        messages.error(request, msg)

    return redirect("versus:detail", pk=pk)


# ==========================
#  COMMUNITY WEB VIEWS (HTML)
# ==========================

@login_required(login_url="/authenticate/login/")
def community_list(request: HttpRequest) -> HttpResponse:
    my_owned = Community.objects.filter(owner=request.user).first()
    my_joined = Community.objects.filter(members=request.user).first()
    my_current = my_owned or my_joined

    communities = Community.objects.all().order_by("name")

    return render(
        request,
        "versus/community_list.html",
        {
            "communities": communities,
            "my_owned": my_owned,
            "my_joined": my_joined,
            "my_current": my_current,
        },
    )


@login_required(login_url="/authenticate/login/")
def community_detail(request: HttpRequest, pk: int) -> HttpResponse:
    community = get_object_or_404(Community, pk=pk)

    challenges_hosted = community.hosted_challenges.all().order_by("start_at")
    challenges_joined = community.joined_challenges.all().order_by("start_at")

    is_owner = community.owner_id == request.user.id
    is_member = community.members.filter(pk=request.user.pk).exists()
    in_this = is_owner or is_member

    return render(
        request,
        "versus/community_detail.html",
        {
            "community": community,
            "challenges_hosted": challenges_hosted,
            "challenges_joined": challenges_joined,
            "is_owner": is_owner,
            "is_member": is_member,
            "in_this": in_this,
        },
    )


@login_required(login_url="/authenticate/login/")
def create_community(request: HttpRequest) -> HttpResponse:
    has_any = (
        not request.user.is_superuser
        and (
            Community.objects.filter(owner=request.user).exists()
            or Community.objects.filter(members=request.user).exists()
        )
    )
    if has_any:
        messages.info(
            request,
            "Kamu sudah tergabung di sebuah community, tidak bisa membuat lagi. "
            "Silakan leave community dulu jika ingin pindah.",
        )
        return redirect("versus:community_list")

    if request.method == "POST":
        form = CommunityForm(request.POST)
        if form.is_valid():
            comm: Community = form.save(commit=False)
            comm.owner = request.user
            comm.save()
            comm.members.add(request.user)
            messages.success(request, "Community berhasil dibuat.")
            return redirect("versus:community_detail", comm.pk)
    else:
        form = CommunityForm()

    return render(
        request,
        "versus/community_form.html",
        {"form": form, "is_edit": False, "community": None},
    )


@login_required(login_url="/authenticate/login/")
def update_community(request: HttpRequest, pk: int) -> HttpResponse:
    community = get_object_or_404(Community, pk=pk)

    if not (request.user.is_superuser or community.owner_id == request.user.id):
        messages.error(request, "Kamu bukan owner community ini.")
        return redirect("versus:community_detail", pk=pk)

    if request.method == "POST":
        form = CommunityForm(request.POST, instance=community)
        if form.is_valid():
            form.save()
            messages.success(request, "Community berhasil diupdate.")
            return redirect("versus:community_detail", pk=pk)
    else:
        form = CommunityForm(instance=community)

    return render(
        request,
        "versus/community_form.html",
        {"form": form, "is_edit": True, "community": community},
    )


@login_required(login_url="/authenticate/login/")
def delete_community(request: HttpRequest, pk: int) -> HttpResponse:
    community = get_object_or_404(Community, pk=pk)

    if not (request.user.is_superuser or community.owner_id == request.user.id):
        messages.error(request, "Kamu bukan owner community ini.")
        return redirect("versus:community_detail", pk=pk)

    if request.method == "POST":
        name = community.name
        community.delete()
        messages.success(request, f"Community '{name}' berhasil dihapus.")
        return redirect("versus:community_list")

    return render(
        request,
        "versus/community_confirm_delete.html",
        {"community": community},
    )


@login_required(login_url="/authenticate/login/")
@require_POST
def join_community(request: HttpRequest, pk: int) -> HttpResponse:
    has_any = (
        not request.user.is_superuser
        and (
            Community.objects.filter(owner=request.user).exists()
            or Community.objects.filter(members=request.user).exists()
        )
    )
    if has_any:
        messages.error(
            request,
            "Kamu sudah tergabung di sebuah community dan tidak bisa join community lain. "
            "Gunakan tombol Leave community jika ingin pindah.",
        )
        return redirect("versus:community_list")

    community = get_object_or_404(Community, pk=pk)
    community.members.add(request.user)
    messages.success(request, f"Kamu berhasil join community {community.name}.")
    return redirect("versus:community_detail", pk=pk)


@login_required(login_url="/authenticate/login/")
@require_POST
def leave_community(request: HttpRequest) -> HttpResponse:
    my_owned = Community.objects.filter(owner=request.user).first()
    my_joined = Community.objects.filter(members=request.user).first()
    current = my_owned or my_joined

    if not current:
        messages.info(request, "Kamu belum tergabung di community manapun.")
        return redirect("versus:community_list")

    if my_owned and my_owned == current:
        other_members = current.members.exclude(pk=request.user.pk)
        if other_members.exists():
            new_owner = other_members.first()
            current.owner = new_owner
            current.save(update_fields=["owner"])
            current.members.add(new_owner)
            current.members.remove(request.user)
            messages.success(
                request,
                f"Kamu keluar dari community. Ownership berpindah ke {new_owner.username}.",
            )
        else:
            name = current.name
            current.delete()
            messages.success(
                request,
                f"Community '{name}' dihapus karena tidak ada anggota lain.",
            )
    else:
        current.members.remove(request.user)
        messages.success(request, "Kamu telah keluar dari community.")

    return redirect("versus:community_list")


# ==========================
#  API CHALLENGE (FLUTTER)
# ==========================

@require_GET
def api_challenge_list(request: HttpRequest) -> JsonResponse:
    sport_q = (request.GET.get("sport") or "").strip().lower()

    qs = Challenge.objects.all().order_by("start_at")
    if sport_q:
        qs = qs.filter(sport=sport_q)

    user = _resolve_user_from_request(request)  # bisa None/anon
    data = [_serialize_challenge(ch, user=user) for ch in qs]
    return JsonResponse(data, safe=False)


@require_GET
def api_challenge_detail(request: HttpRequest, pk: int) -> JsonResponse:
    ch = get_object_or_404(Challenge, pk=pk)
    user = _resolve_user_from_request(request)  # bisa None/anon
    return JsonResponse(_serialize_challenge(ch, user=user))


@csrf_exempt
@require_POST
def api_create_challenge(request: HttpRequest) -> JsonResponse:
    user, err = _json_get_user_or_401(request)
    if err:
        return err

    community = _get_user_community(user)
    if not community:
        return JsonResponse(
            {"ok": False, "status": "error", "message": "Kamu perlu membuat/join community terlebih dahulu."},
            status=400,
        )

    data = _get_request_data(request)
    form = ChallengeCreateForm(data, community=community)
    if not form.is_valid():
        return JsonResponse(
            {"ok": False, "status": "error", "message": "Data tidak valid.", "errors": form.errors},
            status=400,
        )

    ch = form.save_new()
    return JsonResponse(
        {"ok": True, "status": "success", "message": "Matchup berhasil dibuat.", "challenge": _serialize_challenge(ch, user=user)}
    )


@csrf_exempt
@require_POST
def api_update_challenge(request: HttpRequest, pk: int) -> JsonResponse:
    """
    ✅ UPDATE matchup (HANYA owner dari host community / superuser).
    """
    user, err = _json_get_user_or_401(request)
    if err:
        return err

    ch = get_object_or_404(Challenge, pk=pk)

    if not _can_manage_challenge(user, ch):
        return JsonResponse(
            {"ok": False, "status": "error", "message": "Kamu tidak memiliki akses untuk mengedit matchup ini."},
            status=403,
        )

    data = _get_request_data(request)
    form = ChallengeCreateForm(data, community=ch.host)
    if not form.is_valid():
        return JsonResponse(
            {"ok": False, "status": "error", "message": "Data tidak valid.", "errors": form.errors},
            status=400,
        )

    form.apply_to_instance(ch)
    return JsonResponse(
        {"ok": True, "status": "success", "message": "Matchup berhasil diupdate.", "challenge": _serialize_challenge(ch, user=user)}
    )


@csrf_exempt
@require_POST
def api_delete_challenge(request: HttpRequest, pk: int) -> JsonResponse:
    """
    ✅ DELETE matchup (HANYA owner dari host community / superuser).
    """
    user, err = _json_get_user_or_401(request)
    if err:
        return err

    ch = get_object_or_404(Challenge, pk=pk)

    if not _can_manage_challenge(user, ch):
        return JsonResponse(
            {"ok": False, "status": "error", "message": "Kamu tidak memiliki akses untuk menghapus matchup ini."},
            status=403,
        )

    title = ch.title
    ch.delete()
    return JsonResponse(
        {"ok": True, "status": "success", "message": f"Matchup '{title}' berhasil dihapus."},
        status=200,
    )


@csrf_exempt
@require_POST
def api_join_challenge(request: HttpRequest, pk: int) -> JsonResponse:
    user, err = _json_get_user_or_401(request)
    if err:
        return err

    community = _get_user_community(user)
    if not community:
        return JsonResponse(
            {"ok": False, "status": "error", "message": "Kamu perlu membuat/join community terlebih dahulu."},
            status=400,
        )

    ch = get_object_or_404(Challenge, pk=pk)

    ok, msg = _perform_join_for_community(ch, community)
    if not ok:
        return JsonResponse({"ok": False, "status": "error", "message": msg}, status=400)

    return JsonResponse(
        {"ok": True, "status": "success", "message": msg, "challenge": _serialize_challenge(ch, user=user)},
        status=200,
    )


# ==========================
#  API COMMUNITY (FLUTTER)
# ==========================

@require_GET
def api_community_list(request: HttpRequest) -> JsonResponse:
    """
    List semua community + info community yang sedang user ikuti.
    Bisa diakses guest (user anonim).
    """
    user = request.user if request.user.is_authenticated else None

    my_owned = Community.objects.filter(owner=user).first() if user else None
    my_joined = Community.objects.filter(members=user).first() if user else None
    my_current = my_owned or my_joined

    communities = Community.objects.all().order_by("name")

    return JsonResponse(
        {
            "ok": True,
            "status": "success",
            "my_owned": _serialize_community(my_owned, user) if my_owned else None,
            "my_joined": _serialize_community(my_joined, user) if my_joined else None,
            "my_current": _serialize_community(my_current, user) if my_current else None,
            "communities": [
                {
                    **_serialize_community(comm, user),
                    "is_my_current": bool(my_current and my_current.pk == comm.pk),
                }
                for comm in communities
            ],
        }
    )


@require_GET
def api_community_detail(request: HttpRequest, pk: int) -> JsonResponse:
    """
    Detail community + daftar hosted/joined challenges.
    Bisa diakses guest.
    """
    user = request.user if request.user.is_authenticated else None
    community = get_object_or_404(Community, pk=pk)

    challenges_hosted = community.hosted_challenges.all().order_by("start_at")
    challenges_joined = community.joined_challenges.all().order_by("start_at")

    return JsonResponse(
        {
            "ok": True,
            "status": "success",
            "community": _serialize_community(community, user),
            "challenges_hosted": [_serialize_challenge(ch, user=user) for ch in challenges_hosted],
            "challenges_joined": [_serialize_challenge(ch, user=user) for ch in challenges_joined],
        }
    )


@csrf_exempt
@require_POST
def api_community_create(request: HttpRequest) -> JsonResponse:
    user, err = _json_get_user_or_401(request)
    if err:
        return err

    has_any = (
        not user.is_superuser
        and (
            Community.objects.filter(owner=user).exists()
            or Community.objects.filter(members=user).exists()
        )
    )
    if has_any:
        return JsonResponse(
            {"ok": False, "status": "error", "message": "Kamu sudah tergabung di sebuah community, leave dulu jika ingin buat yang baru."},
            status=400,
        )

    data = _get_request_data(request)
    form = CommunityForm(data)
    if not form.is_valid():
        return JsonResponse(
            {"ok": False, "status": "error", "message": "Data tidak valid.", "errors": form.errors},
            status=400,
        )

    comm: Community = form.save(commit=False)
    comm.owner = user
    comm.save()
    comm.members.add(user)

    return JsonResponse(
        {"ok": True, "status": "success", "message": "Community berhasil dibuat.", "community": _serialize_community(comm, user)}
    )


@csrf_exempt
@require_POST
def api_community_update(request: HttpRequest, pk: int) -> JsonResponse:
    user, err = _json_get_user_or_401(request)
    if err:
        return err

    comm = get_object_or_404(Community, pk=pk)
    if not (user.is_superuser or comm.owner_id == user.id):
        return JsonResponse({"ok": False, "status": "error", "message": "Kamu bukan owner community ini."}, status=403)

    data = _get_request_data(request)
    form = CommunityForm(data, instance=comm)
    if not form.is_valid():
        return JsonResponse(
            {"ok": False, "status": "error", "message": "Data tidak valid.", "errors": form.errors},
            status=400,
        )

    comm = form.save()
    return JsonResponse(
        {"ok": True, "status": "success", "message": "Community berhasil diupdate.", "community": _serialize_community(comm, user)}
    )


@csrf_exempt
@require_POST
def api_community_delete(request: HttpRequest, pk: int) -> JsonResponse:
    user, err = _json_get_user_or_401(request)
    if err:
        return err

    comm = get_object_or_404(Community, pk=pk)
    if not (user.is_superuser or comm.owner_id == user.id):
        return JsonResponse({"ok": False, "status": "error", "message": "Kamu bukan owner community ini."}, status=403)

    name = comm.name
    comm.delete()
    return JsonResponse({"ok": True, "status": "success", "message": f"Community '{name}' dihapus."})


@csrf_exempt
@require_POST
def api_community_join(request: HttpRequest, pk: int) -> JsonResponse:
    user, err = _json_get_user_or_401(request)
    if err:
        return err

    has_any = (
        not user.is_superuser
        and (
            Community.objects.filter(owner=user).exists()
            or Community.objects.filter(members=user).exists()
        )
    )
    if has_any:
        return JsonResponse(
            {"ok": False, "status": "error", "message": "Kamu sudah tergabung di community lain. Leave dulu kalau mau pindah."},
            status=400,
        )

    comm = get_object_or_404(Community, pk=pk)
    comm.members.add(user)

    return JsonResponse(
        {"ok": True, "status": "success", "message": f"Kamu berhasil join community {comm.name}.", "community": _serialize_community(comm, user)}
    )


@csrf_exempt
@require_POST
def api_community_leave(request: HttpRequest) -> JsonResponse:
    user, err = _json_get_user_or_401(request)
    if err:
        return err

    my_owned = Community.objects.filter(owner=user).first()
    my_joined = Community.objects.filter(members=user).first()
    current = my_owned or my_joined

    if not current:
        return JsonResponse({"ok": False, "status": "error", "message": "Kamu belum tergabung di community manapun."}, status=400)

    if my_owned and my_owned == current:
        other_members = current.members.exclude(pk=user.pk)
        if other_members.exists():
            new_owner = other_members.first()
            current.owner = new_owner
            current.save(update_fields=["owner"])
            current.members.add(new_owner)
            current.members.remove(user)
            msg = f"Kamu keluar dari community. Ownership berpindah ke {new_owner.username}."
        else:
            name = current.name
            current.delete()
            msg = f"Community '{name}' dihapus karena tidak ada anggota lain."
    else:
        current.members.remove(user)
        msg = "Kamu telah keluar dari community."

    return JsonResponse({"ok": True, "status": "success", "message": msg})