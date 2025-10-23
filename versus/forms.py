# versus/forms.py
from __future__ import annotations
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

from django import forms
from django.apps import apps
from django.core.exceptions import ValidationError

from .models import Challenge, SportChoices, Community

def _dt_formats():
    return [
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%dT%H:%M:%S",
    ]


def _get_datetime_input_formats() -> list[str]:
    """
    Mengakomodasi input manual dan HTML5 datetime-local.
    """
    return [
        "%Y-%m-%d %H:%M",      # 2025-10-08 20:00
        "%Y-%m-%d %H:%M:%S",   # 2025-10-08 20:00:00
        "%Y-%m-%dT%H:%M",      # 2025-10-08T20:00 (datetime-local)
        "%Y-%m-%dT%H:%M:%S",   # 2025-10-08T20:00:00
    ]


class ChallengeCreateForm(forms.Form):
    """
    Form pembuatan Challenge versi lengkap.
    Akan menambahkan field `venue` hanya jika app 'venues' terinstal.
    WAJIB diberi argumen `community` di __init__.
    """
    title = forms.CharField(
        max_length=180,
        label="Judul",
        widget=forms.TextInput(attrs={"placeholder": "Contoh: Friendly Match Komunitas"})
    )

    sport = forms.ChoiceField(
        choices=SportChoices.choices,
        label="Olahraga",
    )

    start_at = forms.DateTimeField(
        label="Waktu mulai",
        input_formats=_get_datetime_input_formats(),
        help_text="Contoh: 2025-10-08 20:00 atau gunakan input datetime-local."
    )

    cost_per_person = forms.IntegerField(
        label="Harga per orang",
        min_value=0,
        required=False,
        initial=0,
        help_text="Boleh 0 jika gratis."
    )

    def __init__(self, *args, **kwargs):
        # community wajib diberikan dari view
        self.community: Community = kwargs.pop("community")
        super().__init__(*args, **kwargs)

        # Tambahkan venue hanya jika app 'venues' ada
        if apps.is_installed("venues"):
            Venue = apps.get_model("venues", "Venue")
            self.fields["venue"] = forms.ModelChoiceField(
                label="Venue",
                queryset=Venue.objects.all(),
                required=False,
                empty_label="(Tanpa venue)"
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

    def save(self, *, commit: bool = True) -> Challenge:
        """
        Membuat Challenge baru.
        """
        data = self.cleaned_data
        ch = Challenge(
            title=data["title"],
            sport=data["sport"],
            host=self.community,
            start_at=data["start_at"],
            cost_per_person=data.get("cost_per_person") or 0,
        )
        # venue opsional — hanya jika field tersedia (app venues terinstal)
        if "venue" in self.fields:
            ch.venue = data.get("venue")

        ch.full_clean()  # validasi model-level
        if commit:
            ch.save()
        return ch


class QuickChallengeForm(forms.Form):
    """
    Form ringkas untuk membuat Challenge tanpa venue,
    sekarang menerima pilihan olahraga.
    Wajib diberi argumen `community` saat init.
    """
    sport = forms.ChoiceField(
        label="Olahraga",
        choices=SportChoices.choices,
        initial=SportChoices.SEPAK_BOLA,
    )
    start_at = forms.DateTimeField(
        label="Waktu mulai",
        input_formats=_dt_formats(),
        help_text="Contoh: 2025-10-08 20:00 atau gunakan input datetime-local."
    )
    cost_per_person = forms.IntegerField(
        label="Harga per orang",
        min_value=0,
        required=False,
        initial=0,
        help_text="Boleh 0 jika gratis."
    )

    def __init__(self, *args, **kwargs):
        self.community: Community = kwargs.pop("community")
        super().__init__(*args, **kwargs)
        # Styling helper (opsional, agar rapi di template)
        self.fields["sport"].widget.attrs.update({"class": "w-full rounded-lg border border-gray-300 px-3 py-2"})
        self.fields["start_at"].widget = forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "w-full rounded-lg border border-gray-300 px-3 py-2"},
            format="%Y-%m-%dT%H:%M",
        )
        self.fields["cost_per_person"].widget.attrs.update({"class": "w-full rounded-lg border border-gray-300 px-3 py-2", "min": "0"})

    def clean_cost_per_person(self):
        value = self.cleaned_data.get("cost_per_person") or 0
        if value < 0:
            raise ValidationError("Harga tidak boleh negatif.")
        return value

    def save(self, *, commit: bool = True) -> Challenge:
        data = self.cleaned_data
        ch = Challenge(
            title="Matchup",
            sport=data["sport"],                # <-- ambil dari pilihan user
            host=self.community,
            start_at=data["start_at"],
            cost_per_person=data.get("cost_per_person") or 0,
        )
        ch.full_clean()
        if commit:
            ch.save()
        return ch
    
def join_challenge(request, pk: int):
    """
    Join VERSUS: set status -> closed.
    Tidak butuh login. POST-only demi keamanan.
    """
    ch = get_object_or_404(Challenge, pk=pk)

    if request.method != "POST":
        # Arahkan balik ke detail kalau bukan POST
        return redirect("versus:detail", pk=pk)

    # Hanya ubah jika masih open
    if (ch.status or "").lower() == "open":
        ch.status = "closed"  # pakai string langsung agar aman meski enum tidak diimport
        # (opsional) set opponent ke Public apabila kamu ingin menandai ada pihak penantang
        # from .views import _get_public_community
        # ch.opponent = _get_public_community()
        ch.save()
        messages.success(request, "Berhasil join. Matchup ditutup (closed).")
    else:
        messages.info(request, "Matchup sudah tidak open.")

    return redirect("versus:detail", pk=pk)