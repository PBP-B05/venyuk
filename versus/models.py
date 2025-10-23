# versus/models.py
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

class SportChoices(models.TextChoices):
    SEPAK_BOLA = ("sepak bola", "Sepak Bola")
    FUTSAL = ("futsal", "Futsal")
    MINI_SOCCER = ("mini soccer", "Mini Soccer")
    BASKETBALL = ("basketball", "Basketball")
    TENNIS = ("tennis", "Tennis")
    BADMINTON = ("badminton", "Badminton")
    PADEL = ("padel", "Padel")
    PICKLE_BALL = ("pickle ball", "Pickle Ball")
    SQUASH = ("squash", "Squash")
    VOLI = ("voli", "Voli")
    BILIARD = ("biliard", "Biliard")
    GOLF = ("golf", "Golf")
    SHOOTING = ("shooting", "Shooting")
    TENNIS_MEJA = ("tennis meja", "Tennis Meja")

class Community(models.Model):
    """Akun komunitas (punya 1 owner User)."""
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=120, unique=True)
    # kalau komunitas multi-olahraga: ganti ke ManyToMany.
    primary_sport = models.CharField(max_length=20, choices=SportChoices.choices)
    logo = models.ImageField(upload_to="community_logo/", blank=True, null=True)

    def __str__(self):
        return self.name

class Challenge(models.Model):
    """Tantangan sparing yang 'OPEN' sampai ada lawan yang join."""
    class Status(models.TextChoices):
        OPEN = ("OPEN", "Open")
        MATCHED = ("MATCHED", "Matched")
        CANCELLED = ("CANCELLED", "Cancelled")
        DONE = ("DONE", "Done")

    title = models.CharField(max_length=180)
    sport = models.CharField(max_length=20, choices=SportChoices.choices)
    host = models.ForeignKey(Community, on_delete=models.CASCADE, related_name="hosted_challenges")
    venue = models.ForeignKey("venues.Venue", on_delete=models.SET_NULL, null=True, blank=True)
    start_at = models.DateTimeField()
    cost_per_person = models.PositiveIntegerField(default=0)  # Rp
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        if self.start_at <= timezone.now():
            raise ValidationError("Jadwal harus di masa depan.")
        if self.host.primary_sport != self.sport:
            raise ValidationError("Sport challenge harus sesuai sport komunitas host.")

    def __str__(self):
        return f"{self.title} ({self.get_sport_display()})"

class Participation(models.Model):
    """Siapa saja yang terlibat pada suatu challenge."""
    class Role(models.TextChoices):
        HOST = ("HOST", "Host")
        GUEST = ("GUEST", "Guest")

    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name="participants")
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name="participations")
    role = models.CharField(max_length=5, choices=Role.choices)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("challenge", "community")

    def clean(self):
        # Pastikan sport community cocok dengan sport challenge
        if self.community.primary_sport != self.challenge.sport:
            raise ValidationError("Sport komunitas harus sesuai dengan sport challenge.")
        # Tidak boleh host join sebagai guest
        if self.role == self.Role.GUEST and self.challenge.host_id == self.community_id:
            raise ValidationError("Host tidak bisa join sebagai Guest.")

    def __str__(self):
        return f"{self.community} -> {self.challenge} ({self.role})"
