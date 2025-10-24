from django import forms
from .models import Promo

class DateInput(forms.DateInput):
    """
    Widget kustom untuk menggunakan input type="date" di HTML.
    """
    input_type = 'date'

class PromoForm(forms.ModelForm):
    """
    ModelForm untuk Promo untuk menggunakan widget kustom.
    """
    class Meta:
        model = Promo
        fields = [
            'title', 'thumbnail', 'description', 'amount_discount', 
            'category', 'max_uses', 'start_date', 'end_date', 'is_active'
        ]
        widgets = {
            'start_date': DateInput(),
            'end_date': DateInput(),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
        help_texts = {
            'start_date': 'Format: YYYY-MM-DD',
            'end_date': 'Format: YYYY-MM-DD',
        }
