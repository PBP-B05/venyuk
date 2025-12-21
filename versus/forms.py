from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError
from django.apps import apps

from .models import Challenge, SportChoices, Community


def _dt_formats() -> list[str]:
    """
    Format datetime yang support input manual dan HTML5 datetime-local.
    """
    return [
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%dT%H:%M:%S",
    ]


class ChallengeCreateForm(forms.Form):
    """
    Form pembuatan / pengeditan Challenge.

    Wajib diberi argumen `community` saat di-init dari view (host community).
    """

    title = forms.CharField(
        max_length=160,
        label="Judul",
        widget=forms.TextInput(
            attrs={"placeholder": "Contoh: Friendly Match Minggu Malam"}
        ),
    )

    sport = forms.ChoiceField(
        label="Olahraga",
        choices=SportChoices.choices,
        initial=SportChoices.SEPAK_BOLA,
    )

    match_category = forms.ChoiceField(
        label="Kategori pertandingan",
        choices=Challenge.MatchCategory.choices,
        initial=Challenge.MatchCategory.LEAGUE,
    )

    start_at = forms.DateTimeField(
        label="Waktu mulai",
        input_formats=_dt_formats(),
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        help_text="Contoh: 2025-10-08 20:00 atau pakai input datetime-local.",
    )

    venue_name = forms.CharField(
        label="Nama venue",
        max_length=120,
        required=False,
    )

    cost_per_person = forms.IntegerField(
        label="Biaya per orang (Rp)",
        min_value=0,
        required=False,
        initial=0,
        help_text="Boleh 0 jika gratis.",
    )

    prize_pool = forms.IntegerField(
        label="Prize pool total (Rp)",
        min_value=0,
        required=False,
        initial=0,
    )

    description = forms.CharField(
        label="Deskripsi",
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
    )

    poster_url = forms.URLField(
        label="Poster (URL)",
        required=False,
        help_text="Opsional, URL gambar poster.",
    )

    def __init__(self, *args, **kwargs):
        self.community: Community = kwargs.pop("community")
        super().__init__(*args, **kwargs)

        if apps.is_installed("venue"):
            Venue = apps.get_model("venue", "Venue")
            self.fields["venue"] = forms.ModelChoiceField(
                label="Venue",
                queryset=Venue.objects.all().order_by("name"),
                required=False,
                empty_label="Pilih venue",
            )

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if not title:
            raise ValidationError("Judul tidak boleh kosong.")
        return title

    def clean_cost_per_person(self):
        value = self.cleaned_data.get("cost_per_person") or 0
        if value < 0:
            raise ValidationError("Harga tidak boleh negatif.")
        return value

    def clean_prize_pool(self):
        value = self.cleaned_data.get("prize_pool") or 0
        if value < 0:
            raise ValidationError("Prize pool tidak boleh negatif.")
        return value

    def save_new(self, *, commit: bool = True) -> Challenge:
        """
        Dipakai untuk CREATE: selalu buat Challenge baru.
        """
        data = self.cleaned_data

        ch = Challenge(
            title=data["title"],
            sport=data["sport"],
            match_category=data["match_category"],
            host=self.community,
            start_at=data["start_at"],
            players_joined=1,
            venue_name=data.get("venue_name") or "",
            cost_per_person=data.get("cost_per_person") or 0,
            prize_pool=data.get("prize_pool") or 0,
            banner_url=data.get("poster_url") or "",
            description=data.get("description") or "",
        )
        if "venue" in self.fields:
            ch.venue = data.get("venue")
            if ch.venue is not None and getattr(ch.venue, "name", None):
                ch.venue_name = ch.venue.name

        ch.full_clean()
        if commit:
            ch.save()
        return ch

    def apply_to_instance(self, instance: Challenge, *, commit: bool = True) -> Challenge:
        """
        Dipakai untuk UPDATE: update instance yang sudah ada.
        Tidak mengubah host, players_joined secara manual, tapi
        boleh mengubah status jika kapasitas berubah (re-open match).
        """
        data = self.cleaned_data

        instance.title = data["title"]
        instance.sport = data["sport"]
        instance.match_category = data["match_category"]
        instance.start_at = data["start_at"]
        instance.cost_per_person = data.get("cost_per_person") or 0
        instance.prize_pool = data.get("prize_pool") or 0
        instance.banner_url = data.get("poster_url") or ""
        instance.description = data.get("description") or ""

        # Venue
        if "venue" in self.fields:
            instance.venue = data.get("venue")
            if instance.venue is not None and getattr(instance.venue, "name", None):
                instance.venue_name = instance.venue.name
            else:
                instance.venue_name = data.get("venue_name") or ""
        else:
            instance.venue = None
            instance.venue_name = data.get("venue_name") or ""

        cap = instance.get_stage_community_size() or 0
        if (
            instance.status == Challenge.Status.CLOSED
            and cap
            and (instance.players_joined or 0) < cap
        ):
            instance.status = Challenge.Status.OPEN

        instance.full_clean()
        if commit:
            instance.save()
        return instance


class CommunityForm(forms.ModelForm):
    class Meta:
        model = Community
        fields = ("name", "primary_sport", "bio")
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 px-3 py-2",
                    "placeholder": "Nama komunitas (mis. FC Depok Sunday League)",
                }
            ),
            "primary_sport": forms.Select(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 px-3 py-2",
                }
            ),
            "bio": forms.Textarea(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 px-3 py-2",
                    "rows": 3,
                    "placeholder": "Deskripsi singkat komunitas...",
                }
            ),
        }


class QuickChallengeForm(forms.Form):
    sport = forms.ChoiceField(
        label="Olahraga",
        choices=SportChoices.choices,
        initial=SportChoices.SEPAK_BOLA,
    )
    start_at = forms.DateTimeField(
        label="Waktu mulai",
        input_formats=_dt_formats(),
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )
    cost_per_person = forms.IntegerField(
        label="Biaya per orang (Rp)",
        min_value=0,
        required=False,
        initial=0,
    )

    def __init__(self, *args, **kwargs):
        self.community: Community = kwargs.pop("community")
        super().__init__(*args, **kwargs)

    def clean_cost_per_person(self):
        value = self.cleaned_data.get("cost_per_person") or 0
        if value < 0:
            raise ValidationError("Harga tidak boleh negatif.")
        return value

    def save(self, *, commit: bool = True) -> Challenge:
        data = self.cleaned_data
        ch = Challenge(
            title="Matchup",
            sport=data["sport"],
            host=self.community,
            start_at=data["start_at"],
            players_joined=1,  # host = 1 community
            cost_per_person=data.get("cost_per_person") or 0,
        )
        ch.full_clean()
        if commit:
            ch.save()
        return ch
