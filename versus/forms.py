from __future__ import annotations
from django import forms
from django.core.exceptions import ValidationError
from .models import Challenge, SportChoices, Community

def _dt_formats():
    return [
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%dT%H:%M:%S",
    ]


class ChallengeCreateForm(forms.Form):
    title = forms.CharField(
        max_length=180,
        label="Match Title",
        widget=forms.TextInput(attrs={
            "placeholder": "Contoh: Friendly Match Komunitas",
            "class": "w-full rounded-lg border border-gray-300 px-3 py-2",
        }),
    )

    sport = forms.ChoiceField(
        choices=SportChoices.choices,
        label="Olahraga",
        widget=forms.Select(attrs={"class": "w-full rounded-lg border border-gray-300 px-3 py-2"}),
    )

    match_category = forms.ChoiceField(
        choices=Challenge.MatchCategory.choices,
        initial=Challenge.MatchCategory.LEAGUE,
        label="Kategori",
        widget=forms.Select(attrs={"class": "w-full rounded-lg border border-gray-300 px-3 py-2"}),
    )

    start_at = forms.DateTimeField(
        label="Waktu mulai",
        input_formats=[
            "%Y-%m-%d %H:%M","%Y-%m-%d %H:%M:%S","%Y-%m-%dT%H:%M","%Y-%m-%dT%H:%M:%S",
        ],
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local","class": "w-full rounded-lg border border-gray-300 px-3 py-2"},
            format="%Y-%m-%dT%H:%M",
        ),
    )

    venue_name = forms.CharField(
        required=False,
        label="Venue",
        widget=forms.TextInput(attrs={
            "placeholder": "Contoh: Lapangan ABC, Jakarta",
            "class": "w-full rounded-lg border border-gray-300 px-3 py-2",
        }),
    )

    cost_per_person = forms.IntegerField(
        label="Harga (per orang)",
        min_value=0,
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={"class": "w-full rounded-lg border border-gray-300 px-3 py-2","min": "0"}),
    )

    prize_pool = forms.IntegerField(
        label="Prize Pool (Rp)",
        min_value=0,
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={"class": "w-full rounded-lg border border-gray-300 px-3 py-2","min": "0"}),
    )

    banner_url = forms.URLField(
        required=False,
        label="Poster Image (URL)",
        help_text="Tempel tautan gambar (https://...)",
        widget=forms.URLInput(attrs={
            "placeholder": "https://example.com/poster.jpg",
            "class": "w-full rounded-lg border border-gray-300 px-3 py-2",
        }),
    )

    description = forms.CharField(
        required=False,
        label="Deskripsi",
        widget=forms.Textarea(attrs={
            "rows": 4,
            "placeholder": "Tulis deskripsi singkat pertandingan…",
            "class": "w-full rounded-lg border border-gray-300 px-3 py-2",
        }),
    )

    def __init__(self, *args, **kwargs):
        self.community: Community = kwargs.pop("community")
        super().__init__(*args, **kwargs)

    def save(self, *, commit: bool = True) -> Challenge:
        d = self.cleaned_data
        ch = Challenge(
            title=d["title"],
            sport=d["sport"],
            match_category=d["match_category"],
            host=self.community,
            start_at=d["start_at"],
            venue_name=d.get("venue_name") or "",
            cost_per_person=d.get("cost_per_person") or 0,
            prize_pool=d.get("prize_pool") or 0,
            banner_url=d.get("banner_url") or "",     
            description=d.get("description") or "",   
        )
        ch.full_clean()
        if commit:
            ch.save()
        return ch


class QuickChallengeForm(forms.Form):
    """Form ringkas (opsional)."""
    sport = forms.ChoiceField(
        label="Olahraga",
        choices=SportChoices.choices,
        initial=SportChoices.SEPAK_BOLA,
        widget=forms.Select(attrs={
            "class": "w-full rounded-lg border border-gray-300 px-3 py-2",
        }),
    )
    match_category = forms.ChoiceField(
        label="Kategori Matchup",
        choices=Challenge.MatchCategory.choices,   
        initial=Challenge.MatchCategory.LEAGUE,
        widget=forms.Select(attrs={
            "class": "w-full rounded-lg border border-gray-300 px-3 py-2",
        }),
    )
    start_at = forms.DateTimeField(
        label="Waktu mulai",
        input_formats=_dt_formats(),
        widget=forms.DateTimeInput(
            attrs={
                "type": "datetime-local",
                "class": "w-full rounded-lg border border-gray-300 px-3 py-2",
            },
            format="%Y-%m-%dT%H:%M",
        ),
    )
    cost_per_person = forms.IntegerField(
        label="Harga per orang",
        min_value=0,
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={
            "class": "w-full rounded-lg border border-gray-300 px-3 py-2",
            "min": "0",
        }),
    )

    def __init__(self, *args, **kwargs):
        self.community: Community = kwargs.pop("community")
        super().__init__(*args, **kwargs)

    def clean_cost_per_person(self):
        v = self.cleaned_data.get("cost_per_person") or 0
        if v < 0:
            raise ValidationError("Harga tidak boleh negatif.")
        return v

    def save(self, *, commit: bool = True) -> Challenge:
        d = self.cleaned_data
        ch = Challenge(
            title="Matchup",
            sport=d["sport"],
            match_category=d["match_category"],
            host=self.community,
            start_at=d["start_at"],
            cost_per_person=d.get("cost_per_person") or 0,
        )
        ch.full_clean()
        if commit:
            ch.save()
        return ch

