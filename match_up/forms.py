from django import forms
from .models import Match

class MatchForm(forms.ModelForm):
    class Meta:
        model = Match
        
        # Tampilkan field yang perlu diisi pengguna
        # 'creator' dan 'slot_terisi' akan diisi otomatis
        fields = ['venue', 'slot_total', 'start_time', 'end_time', 'difficulty_level']
        
        # Tambahan: Widget agar input tanggal dan waktu lebih mudah
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }