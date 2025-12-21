from django import forms
from .models import Promo

class DateInput(forms.DateInput):
    input_type = 'date'

class PromoForm(forms.ModelForm):
    class Meta:
        model = Promo
        fields = [
            'title', 
            'description', 
            'amount_discount', 
            'category', 
            'max_uses', 
            'start_date', 
            'end_date', 
            'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'start_date': DateInput(),
            'end_date': DateInput(),
        }
        
        help_texts = {
            'title': 'Masukkan judul yang menarik untuk promo Anda.',
            'description': 'Jelaskan detail promo dan syarat ketentuan untuk menggunakan promo.',
            'amount_discount': 'Masukkan angka saja (misal: 15 untuk 15%).',
            'is_active': 'Centang agar promo bisa dilihat oleh publik.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        text_inputs = ['title']
        for field_name in text_inputs:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({'class': 'tailwind-text-input-class'})

        date_inputs = ['start_date', 'end_date']
        for field_name in date_inputs:
             if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({'class': 'tailwind-date-input-class'})



