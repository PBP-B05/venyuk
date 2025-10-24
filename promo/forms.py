from django import forms
from django.core.exceptions import ValidationError
from promo.models import Promo

class PromoForm(forms.ModelForm):
    class Meta:
        model = Promo
        fields = [
            'title', 
            'thumbnail', 
            'category', 
            'description', 
            'discount_percentage',
            'start_date', 
            'end_date', 
            'max_uses'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contoh: Promo Spesial Kemerdekaan'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Deskripsi promo...',
                'rows': 4
            }),
            'discount_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contoh: 30',
                'min': 1,
                'max': 100
            }),
            'start_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'end_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'max_uses': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contoh: 100',
                'min': 1
            }),
            'thumbnail': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
        labels = {
            'title': 'Judul Promo',
            'thumbnail': 'Thumbnail',
            'category': 'Kategori',
            'description': 'Deskripsi',
            'discount_percentage': 'Persentase Diskon (%)',
            'start_date': 'Tanggal Mulai',
            'end_date': 'Tanggal Berakhir',
            'max_uses': 'Maksimal Penggunaan'
        }
        help_texts = {
            'discount_percentage': 'Masukkan angka 1-100',
            'max_uses': 'Total penggunaan untuk semua user',
            'thumbnail': 'Format: JPG, PNG, WebP. Maksimal 5MB'
        }
    
    def clean_thumbnail(self):
        """Validasi thumbnail"""
        thumbnail = self.cleaned_data.get('thumbnail')
        if thumbnail:
            # Validasi ukuran file (max 5MB)
            if thumbnail.size > 5 * 1024 * 1024:
                raise ValidationError('Ukuran file maksimal 5MB')
            
            # Validasi format file
            valid_extensions = ['jpg', 'jpeg', 'png', 'webp']
            ext = thumbnail.name.split('.')[-1].lower()
            if ext not in valid_extensions:
                raise ValidationError('Format file harus JPG, PNG, atau WebP')
        
        return thumbnail
    
    def clean_discount_percentage(self):
        """Validasi discount percentage"""
        discount = self.cleaned_data.get('discount_percentage')
        if discount < 1 or discount > 100:
            raise ValidationError('Persentase diskon harus antara 1-100')
        return discount
    
    def clean_max_uses(self):
        """Validasi max uses"""
        max_uses = self.cleaned_data.get('max_uses')
        if max_uses < 1:
            raise ValidationError('Maksimal penggunaan minimal 1')
        return max_uses
    
    def clean(self):
        """Validasi form secara keseluruhan"""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        # Validasi tanggal
        if start_date and end_date:
            if end_date <= start_date:
                raise ValidationError({
                    'end_date': 'Tanggal berakhir harus setelah tanggal mulai'
                })
        
        return cleaned_data