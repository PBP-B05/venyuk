from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .forms import ChallengeCreateForm, CommunityForm
from .models import Challenge, Community, SportChoices



def _get_user_community(user) -> Community | None:
    if not user.is_authenticated:
        return None

    owned = Community.objects.filter(owner=user).first()
    joined = Community.objects.filter(members=user).first()
    return owned or joined


def _ensure_user_community(request: HttpRequest):
    community = _get_user_community(request.user)
    if community is None:
        messages.info(
            request,
            "Kamu perlu membuat atau join community terlebih dahulu sebelum membuat atau join Versus.",
        )
        return None, redirect("versus:community_list")
    return community, None


def _json_requires_login(request: HttpRequest):
    if request.user.is_authenticated:
        return None

    login_url = reverse("authenticate:login")
    return JsonResponse(
        {
            "ok": False,
            "requires_login": True,
            "login_url": login_url,
            "message": "Silakan login terlebih dahulu.",
        },
        status=401,
    )


def _json_requires_community(request: HttpRequest):
    community = _get_user_community(request.user)
    if community is None:
        return None, JsonResponse(
            {
                "ok": False,
                "requires_community": True,
                "community_url": reverse("versus:community_list"),
                "message": "Kamu perlu membuat atau join community terlebih dahulu.",
            },
            status=400,
        )
    return community, None


def _serialize_challenge(ch: Challenge) -> dict:
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
        "players_joined": ch.players_joined or 0,   # jumlah community
        "max_players": ch.max_players,              # kapasitas community
        "detail_url": ch.get_absolute_url(),
        # Community info
        "host_id": ch.host_id,
        "host_name": ch.host.name if ch.host_id else "",
        "opponent_id": ch.opponent_id,
        "opponent_name": ch.opponent.name if ch.opponent_id else "",
        "has_opponent": ch.opponent_id is not None,
        "stage_community_size": ch.get_stage_community_size(),
    }


def _perform_join_for_community(ch: Challenge, community: Community):
    if ch.status != Challenge.Status.OPEN:
        return False, "Matchup sudah tidak open."

    # Kapasitas community sesuai kategori
    cap = ch.get_stage_community_size() or 2

    # Slot sudah penuh
    if ch.players_joined >= cap:
        return False, "Slot community untuk matchup ini sudah penuh."

    # Host tidak boleh join sebagai community tambahan
    if ch.host_id == community.id:
        return False, "Community kamu adalah host matchup ini."

    # Community ini sudah jadi opponent utama
    if ch.opponent_id == community.id:
        return False, "Community kamu sudah terdaftar sebagai opponent di matchup ini."

    # Kalau belum ada opponent, set community ini sebagai opponent 'utama'
    if ch.opponent_id is None:
        ch.opponent = community

    # Tambah jumlah community yang ikut
    ch.players_joined = (ch.players_joined or 0) + 1
    ch.save()

    # Cek apakah perlu di-close (lihat logic di models.py)
    ch.try_close()

    return True, f"Community kamu berhasil join. Total community: {ch.players_joined}/{cap}."


def _ensure_host_owner(request: HttpRequest, ch: Challenge) -> bool:
    u = request.user
    return bool(
        u.is_authenticated and (u.is_superuser or ch.host.owner_id == u.id)
    )



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



@require_GET
def api_challenge_list(request: HttpRequest) -> JsonResponse:
    sport_q = (request.GET.get("sport") or "").strip().lower()

    qs = Challenge.objects.all().order_by("start_at")
    if sport_q:
        qs = qs.filter(sport=sport_q)

    data = [_serialize_challenge(ch) for ch in qs]
    return JsonResponse(data, safe=False)


@require_GET
def api_challenge_detail(request: HttpRequest, pk: int) -> JsonResponse:
    ch = get_object_or_404(Challenge, pk=pk)
    return JsonResponse(_serialize_challenge(ch))


@csrf_exempt
@require_POST
def api_join_challenge(request: HttpRequest, pk: int) -> JsonResponse:
    not_auth = _json_requires_login(request)
    if not_auth:
        return not_auth

    community, err_resp = _json_requires_community(request)
    if err_resp:
        return err_resp

    ch = get_object_or_404(Challenge, pk=pk)

    ok, msg = _perform_join_for_community(ch, community)
    if not ok:
        return JsonResponse({"ok": False, "message": msg}, status=400)

    return JsonResponse(
        {
            "ok": True,
            "message": msg,
            "challenge": _serialize_challenge(ch),
        }
    )



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
        {
            "form": form,
            "is_edit": False,
            "community": None,
        },
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
        {
            "form": form,
            "is_edit": True,
            "community": community,
        },
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
        messages.success(
            request,
            f"Community '{name}' berhasil dihapus.",
        )
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
