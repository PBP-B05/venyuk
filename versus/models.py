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
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="communities",
    )
    name = models.CharField(max_length=120)
    primary_sport = models.CharField(max_length=20, choices=SportChoices.choices)
    bio = models.TextField(blank=True)

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="joined_communities",
        blank=True,
    )

    def __str__(self):
        return self.name

    @property
    def total_members(self) -> int:
        return 1 + self.members.count()


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

    CATEGORY_COMMUNITY_SIZE = {
        MatchCategory.CUP_FINAL: 2,
        MatchCategory.RO16: 16,
        MatchCategory.QUARTER_FINAL: 8,
        MatchCategory.SEMI_FINAL: 4,
        MatchCategory.LEAGUE: 24,
    }

    title = models.CharField(max_length=160)
    sport = models.CharField(max_length=20, choices=SportChoices.choices)
    match_category = models.CharField(
        max_length=20,
        choices=MatchCategory.choices,
        default=MatchCategory.LEAGUE,
    )

    # Community host & opponent (opponent = community pertama yang join)
    host = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name="hosted_challenges",
    )
    opponent = models.ForeignKey(
        Community,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="joined_challenges",
    )

    venue = models.ForeignKey(
        "venue.Venue",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="versus_challenges",
    )
    venue_name = models.CharField(max_length=120, blank=True)

    start_at = models.DateTimeField()
    cost_per_person = models.PositiveIntegerField(null=True, blank=True)
    prize_pool = models.PositiveIntegerField(null=True, blank=True, default=0)

    # JUMLAH COMMUNITY yang ikut (termasuk host)
    players_joined = models.PositiveIntegerField(default=1)

    banner_url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.OPEN,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_at"]

    def __str__(self):
        return f"{self.title} • {self.get_sport_display()}"

    def get_absolute_url(self):
        return reverse("versus:detail", args=[self.pk])

    @property
    def display_venue_name(self) -> str:
        if self.venue_id and getattr(self.venue, "name", None):
            return self.venue.name
        return self.venue_name or ""

    def get_stage_community_size(self) -> int | None:
        return self.CATEGORY_COMMUNITY_SIZE.get(self.match_category)

    @property
    def max_players(self) -> int:
        return self.get_stage_community_size() or 0

    def try_close(self):
        """
        Tutup otomatis kalau jumlah community sudah memenuhi kapasitas kategori
        """
        if self.status != self.Status.OPEN:
            return

        cap = self.get_stage_community_size() or 2
        if self.players_joined >= cap:
            self.status = self.Status.CLOSED
            self.save(update_fields=["status"])




