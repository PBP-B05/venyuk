from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .forms import ChallengeCreateForm
from .models import Challenge, Community, SportChoices


def _get_or_create_user_community(user) -> Community:
    """Community default milik user (dipakai jika login & auth required)."""
    comm, _ = Community.objects.get_or_create(
        owner=user,
        defaults={
            "name": f"{user.username} Community",
            "primary_sport": SportChoices.SEPAK_BOLA,
            "bio": "Default community for this user.",
        },
    )
    return comm

def _get_public_community() -> Community:
    """Community 'Public' (dipakai saat anonim / testing)."""
    User = get_user_model()
    system_user, _ = User.objects.get_or_create(
        username="system",
        defaults={"email": "system@example.com"},
    )
    comm, _ = Community.objects.get_or_create(
        name="Public",
        defaults={
            "owner": system_user,
            "primary_sport": SportChoices.SEPAK_BOLA,
            "bio": "Community default untuk event publik.",
        },
    )
    return comm

def _serialize_challenge(ch: Challenge) -> dict:
    return {
        "id": ch.id,
        "title": ch.title,
        "sport": ch.sport,
        "sport_label": ch.get_sport_display(),
        "match_category": ch.match_category,
        "match_category_label": ch.get_match_category_display(),
        "start_at": ch.start_at.isoformat(),
        "status": ch.status,
        "status_label": ch.get_status_display(),
        "cost_per_person": ch.cost_per_person or 0,
        "prize_pool": ch.prize_pool or 0,
        "venue_name": ch.venue_name or "",
        "players_joined": ch.players_joined or 0,
        "max_players": ch.max_players,
        "detail_url": ch.get_absolute_url(),
    }

def _json_requires_login(request):
    """
    Kembalikan JSON 401 hanya jika login diwajibkan lewat settings.
    Kalau VERSUS_AUTH_REQUIRED=False -> selalu None (bebas).
    """
    if getattr(settings, "VERSUS_AUTH_REQUIRED", False) and not request.user.is_authenticated:
        return JsonResponse(
            {
                "ok": False,
                "requires_login": True,
                "login_url": reverse("authenticate:login"),
                "message": "Harus login untuk melakukan aksi ini.",
            },
            status=401,
        )
    return None


def list_challenges(request):
    """Halaman list + filter (publik)."""
    sport_q = (request.GET.get("sport") or "").strip().lower()
    valid_sports = [val for val, _ in SportChoices.choices]

    qs = Challenge.objects.all().order_by("start_at")
    sport_selected = ""
    if sport_q in valid_sports:
        qs = qs.filter(sport=sport_q)
        sport_selected = sport_q

    context = {
        "challenges": qs,
        "sports": SportChoices.choices,
        "sport_selected": sport_selected,
    }
    return render(request, "versus/list.html", context)


def challenge_detail(request, pk: int):
    """Detail (publik)."""
    ch = get_object_or_404(Challenge, pk=pk)
    return render(request, "versus/detail.html", {"ch": ch})

def create_challenge(request):
    """
    Create Versus.
    - Jika settings.VERSUS_AUTH_REQUIRED=True dan user belum login → redirect ke login.
    - Jika tidak diwajibkan (default False), event akan di-host oleh 'Public'.
    - Jika diwajibkan & user login → host = community user.
    """
    if getattr(settings, "VERSUS_AUTH_REQUIRED", False):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('authenticate:login')}?next={request.path}")
        community = _get_or_create_user_community(request.user)
    else:
        # testing mode / bebas
        community = _get_public_community()

    if request.method == "POST":
        form = ChallengeCreateForm(request.POST, community=community)
        if form.is_valid():
            ch = form.save()
            messages.success(request, "Matchup berhasil dibuat.")
            return redirect("versus:detail", ch.pk)
    else:
        form = ChallengeCreateForm(community=community)

    return render(request, "versus/create.html", {"form": form})


def join_challenge(request, pk: int):
    """
    Join (auth opsional via flag).
    Kalau auth required & belum login → redirect login;
    kalau tidak, tetap boleh join.
    """
    ch = get_object_or_404(Challenge, pk=pk)

    if request.method != "POST":
        return redirect("versus:detail", pk=pk)

    if getattr(settings, "VERSUS_AUTH_REQUIRED", False) and not request.user.is_authenticated:
        return redirect(f"{reverse('authenticate:login')}?next={request.path}")

    if (ch.status or "").lower() != "open":
        messages.info(request, "Matchup sudah tidak open.")
        return redirect("versus:detail", pk=pk)

    ch.players_joined = (ch.players_joined or 0) + 1
    ch.save(update_fields=["players_joined"])
    ch.try_close()

    if (ch.status or "").lower() == "closed":
        messages.success(request, "Kuota terpenuhi. Matchup ditutup (closed).")
    else:
        messages.success(
            request, f"Berhasil join. {ch.players_joined}/{ch.max_players} pemain."
        )
    return redirect("versus:detail", pk=pk)


# ---------- API (list/detail publik; join opsional auth) ----------
@require_GET
def api_challenge_list(request):
    sport_q = (request.GET.get("sport") or "").strip().lower()
    qs = Challenge.objects.all().order_by("start_at")
    if sport_q:
        qs = qs.filter(sport=sport_q)
    data = [_serialize_challenge(ch) for ch in qs]
    return JsonResponse(data, safe=False)


@require_GET
def api_challenge_detail(request, pk: int):
    ch = get_object_or_404(Challenge, pk=pk)
    return JsonResponse(_serialize_challenge(ch))


@csrf_exempt
@require_POST
def api_join_challenge(request, pk: int):
    not_auth = _json_requires_login(request)
    if not_auth:
        return not_auth

    ch = get_object_or_404(Challenge, pk=pk)
    if (ch.status or "").lower() != "open":
        return JsonResponse(
            {"ok": False, "message": "Matchup sudah tidak open."}, status=400
        )

    ch.players_joined = (ch.players_joined or 0) + 1
    ch.save(update_fields=["players_joined"])
    ch.try_close()

    msg = (
        "Kuota terpenuhi. Matchup ditutup (closed)."
        if (ch.status or "").lower() == "closed"
        else f"Berhasil join. {ch.players_joined}/{ch.max_players} pemain."
    )

    return JsonResponse({"ok": True, "message": msg, "challenge": _serialize_challenge(ch)})


