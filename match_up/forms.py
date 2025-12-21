from django import forms
from venue.models import Venue
from .models import Match

class MatchForm(forms.ModelForm):
    
    venue = forms.ModelChoiceField(
        queryset=Venue.objects.filter(is_available=True), 
        empty_label="Pilih venue"
    )
    
    class Meta:
        model = Match
        fields = ['venue', 'slot_total', 'start_time', 'end_time', 'difficulty_level']
        
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }