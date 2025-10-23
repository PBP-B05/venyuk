# versus/views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .models import Challenge, SportChoices, Community
from .forms import QuickChallengeForm
from django.contrib.auth import get_user_model

def list_challenges(request):
    sport = (request.GET.get("sport") or "").strip()
    qs = Challenge.objects.filter(status=Challenge.Status.OPEN)
    if sport:
        qs = qs.filter(sport=sport)
    qs = qs.order_by("start_at")[:12]
    return render(request, "versus/list.html", {
        "challenges": qs,
        "sports": SportChoices.choices,
        "sport_selected": sport,
    })

def challenge_detail(request, pk: int):
    ch = get_object_or_404(Challenge, pk=pk)
    return render(request, "versus/detail.html", {"ch": ch})

def join_challenge(request, pk: int):
    ch = get_object_or_404(Challenge, pk=pk)
    # TODO: implement join logic; sementara notifikasi saja
    messages.success(request, f"Kamu menerima tantangan: {ch.title}")
    return redirect(ch.get_absolute_url())


def create_challenge(request):
    """
    Create Versus TANPA login.
    - Jika user login dan sudah punya Community, bisa diarahkan ke miliknya.
      (opsional; demi konsistensi, di sini kita pakai 'Public' agar simpel)
    - Jika anonim: selalu pakai 'Public'
    """
    # Selalu gunakan Public (paling aman untuk requirement saat ini)
    community = _get_public_community()

    if request.method == "POST":
        form = QuickChallengeForm(request.POST, community=community)
        if form.is_valid():
            ch = form.save()
            messages.success(request, "Matchup berhasil dibuat.")
            # Redirect ke detail jika ada, fallback ke list
            try:
                return redirect(ch.get_absolute_url())
            except Exception:
                return redirect("versus:list")
    else:
        form = QuickChallengeForm(community=community)

    return render(request, "versus/create.html", {"form": form})

def _get_public_community():
    """
    Community default untuk event tanpa login.
    Gunakan field yang ADA di model: owner, name, primary_sport, bio.
    """
    User = get_user_model()
    system_user, _ = User.objects.get_or_create(
        username="system",
        defaults={"email": "system@example.com"}
    )
    comm, _ = Community.objects.get_or_create(
        name="Public",
        defaults={
            "owner": system_user,
            "primary_sport": SportChoices.SEPAK_BOLA,
            "bio": "Community default untuk event publik.",  # <-- was 'description'
        },
    )
    return comm

