from django.db import models
from django.utils import timezone
import uuid
# from django.contrib.auth.models import User # Import User jika Anda ingin melacak siapa yang membuat promo

class Promo(models.Model):
    """
    Model untuk menyimpan data promo.
    Field 'thumbnail' telah dihapus.
    """
    CATEGORY_CHOICES = [
        ('shop', 'Shop'),
        ('venue', 'Venue'),
    ]

    title = models.CharField(max_length=200, help_text="Judul promo, cth: Promo Spesial Kemerdekaan")
    

    description = models.TextField(help_text="Deskripsi lengkap promo")
    amount_discount = models.PositiveSmallIntegerField(help_text="Besar diskon dalam persentase (cth: 20 untuk 20%)")
    
    code = models.CharField(
        max_length=50, 
        unique=True, 
        blank=True, 
        editable=False, 
        help_text="Kode promo unik (dibuat otomatis)"
    )
    
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='venue')
    max_uses = models.PositiveIntegerField(default=100, help_text="Berapa kali promo ini bisa digunakan")
    start_date = models.DateField(default=timezone.now, help_text="Tanggal promo mulai aktif")
    end_date = models.DateField(help_text="Tanggal promo berakhir")
    is_active = models.BooleanField(default=True, help_text="Centang jika promo ini aktif dan bisa dilihat publik")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def is_promo_active(self):
        """
        Helper method untuk mengecek apakah promo sedang dalam masa berlaku.
        """
        now = timezone.now().date()
        return self.is_active and self.start_date <= now <= self.end_date

    def _generate_unique_code(self):
        """
        Helper method internal untuk membuat kode unik.
        Format: [CATEGORY][AMOUNT]-[RANDOM_6_CHAR]
        Contoh: VENUE15-F3E9A1
        """
        while True:
            prefix = f"{self.category.upper()}{self.amount_discount}"
            random_suffix = uuid.uuid4().hex[:6].upper()
            code = f"{prefix}-{random_suffix}"
            if not Promo.objects.filter(code=code).exists():
                return code

    def save(self, *args, **kwargs):
        """
        Override save method untuk membuat kode unik saat pertama kali disimpan.
        """
        if not self.code:
            self.code = self._generate_unique_code()
        
        super().save(*args, **kwargs)

