# versus/models.py
from django.conf import settings
from django.db import models
from django.urls import reverse

class SportChoices(models.TextChoices):
    SEPAK_BOLA   = "sepak bola", "Sepak Bola"
    FUTSAL       = "futsal", "Futsal"
    MINI_SOCCER  = "mini soccer", "Mini Soccer"
    BASKETBALL   = "basketball", "Basketball"
    TENNIS       = "tennis", "Tennis"
    BADMINTON    = "badminton", "Badminton"
    PADEL        = "padel", "Padel"
    PICKLE_BALL  = "pickle ball", "Pickle Ball"
    SQUASH       = "squash", "Squash"
    VOLI         = "voli", "Voli"
    BILIARD      = "biliard", "Biliard"
    GOLF         = "golf", "Golf"
    SHOOTING     = "shooting", "Shooting"
    TENNIS_MEJA  = "tennis meja", "Tennis Meja"

class Community(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="communities")
    name = models.CharField(max_length=120)
    primary_sport = models.CharField(max_length=20, choices=SportChoices.choices)
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Challenge(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"
        COMPLETED = "completed", "Completed"

    # >>> Tambahan: kategori matchup
    class MatchCategory(models.TextChoices):
        RO16          = "RO16", "RO16"
        CUP_FINAL     = "Cup Final", "Cup Final"
        LEAGUE        = "League", "League"
        QUARTER_FINAL = "Quarter Final", "Quarter Final"
        SEMI_FINAL    = "Semi Final", "Semi Final"

    title = models.CharField(max_length=160)
    sport = models.CharField(max_length=20, choices=SportChoices.choices)
    host = models.ForeignKey(Community, on_delete=models.CASCADE, related_name="hosted_challenges")
    opponent = models.ForeignKey(Community, on_delete=models.SET_NULL, null=True, blank=True, related_name="joined_challenges")

    start_at = models.DateTimeField()
    cost_per_person = models.PositiveIntegerField(null=True, blank=True)  # rupiah/orang
    banner_url = models.URLField(blank=True)
    description = models.TextField(blank=True)

    # >>> field baru
    match_category = models.CharField(
        max_length=20,
        choices=MatchCategory.choices,
        default=MatchCategory.LEAGUE,
        verbose_name="Kategori Matchup",
    )

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_at"]

    def __str__(self):
        return f"{self.title} • {self.get_sport_display()}"

    def get_absolute_url(self):
        return reverse("versus:detail", args=[self.pk])
