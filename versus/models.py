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

    class MatchCategory(models.TextChoices):
        RO16          = "ro16", "RO16"
        QUARTER_FINAL = "quarter_final", "Quarter Final"
        SEMI_FINAL    = "semi_final", "Semi Final"
        CUP_FINAL     = "cup_final", "Cup Final"
        LEAGUE        = "league", "League"

    title = models.CharField(max_length=160)
    sport = models.CharField(max_length=20, choices=SportChoices.choices)
    match_category = models.CharField(          
        max_length=20,
        choices=MatchCategory.choices,
        default=MatchCategory.LEAGUE,
    )

    host = models.ForeignKey(Community, on_delete=models.CASCADE, related_name="hosted_challenges")
    opponent = models.ForeignKey(Community, on_delete=models.SET_NULL, null=True, blank=True, related_name="joined_challenges")
    start_at = models.DateTimeField()
    cost_per_person = models.PositiveIntegerField(null=True, blank=True)
    prize_pool = models.PositiveIntegerField(null=True, blank=True, default=0)  
    venue_name = models.CharField(max_length=120, blank=True)                   
    players_joined = models.PositiveIntegerField(default=0)                     
    banner_url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_at"]

    def __str__(self):
        return f"{self.title} • {self.get_sport_display()}"

    def get_absolute_url(self):
        return reverse("versus:detail", args=[self.pk])

    SPORT_MAX = {
        "sepak bola": 22,
        "futsal": 10,
        "mini soccer": 14,
        "basketball": 10,
        "voli": 12,      
        "tennis": 4,     
        "badminton": 4,
        "padel": 4,
        "pickle ball": 4,
        "squash": 4,
        "biliard": 4,
        "golf": 4,       
        "shooting": 1,   
        "tennis meja": 4,
    }

    @property
    def max_players(self) -> int:
        return self.SPORT_MAX.get((self.sport or "").lower(), 0)

    def try_close(self):
        """Tutup otomatis jika kuota terpenuhi."""
        if self.status == self.Status.OPEN and self.players_joined >= self.max_players > 0:
            self.status = self.Status.CLOSED
            self.save(update_fields=["status"])
