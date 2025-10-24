# promo/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import random
import string

def generate_promo_code(category, discount_percentage, start_date):
    """
    Generate unique promo code with format: VENUE30-JAN25-A7B3
    """
    # Category prefix
    category_prefix = category.upper()[:5]  # VENUE or SHOP
    
    # Discount
    discount = f"{discount_percentage}"
    
    # Month-Year from start_date
    month_year = start_date.strftime('%b%y').upper()  # JAN25
    
    # Random unique suffix (4 characters: letters + numbers)
    unique_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    
    # Combine: VENUE30-JAN25-A7B3
    code = f"{category_prefix}{discount}-{month_year}-{unique_suffix}"
    
    # Ensure uniqueness
    while Promo.objects.filter(code=code).exists():
        unique_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        code = f"{category_prefix}{discount}-{month_year}-{unique_suffix}"
    
    return code


class Promo(models.Model):
    CATEGORY_CHOICES = [
        ('venue', 'Venue'),
        ('shop', 'Shop'),
    ]
    
    # Basic Info
    title = models.CharField(max_length=200, verbose_name="Judul Promo")
    code = models.CharField(
        max_length=50, 
        unique=True, 
        blank=True,  # Allow blank for new instances
        verbose_name="Kode Promo"
    )
    thumbnail = models.ImageField(
        upload_to='promos/',
        verbose_name="Thumbnail"
    )
    category = models.CharField(
        max_length=10, 
        choices=CATEGORY_CHOICES, 
        default='venue',
        verbose_name="Kategori"
    )
    description = models.TextField(verbose_name="Deskripsi")
    
    # Discount
    discount_percentage = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name="Persentase Diskon (%)",
        help_text="Masukkan angka 1-100"
    )
    
    # Date Range
    start_date = models.DateTimeField(verbose_name="Tanggal Mulai")
    end_date = models.DateTimeField(verbose_name="Tanggal Berakhir")
    
    # Usage Limits
    max_uses = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Maksimal Penggunaan",
        help_text="Total penggunaan untuk semua user"
    )
    current_uses = models.IntegerField(
        default=0,
        verbose_name="Jumlah Terpakai",
        help_text="Otomatis bertambah saat promo digunakan"
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktif"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='created_promos'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Promo"
        verbose_name_plural = "Promos"
    
    def __str__(self):
        return f"{self.code} - {self.title}"
    
    def save(self, *args, **kwargs):
        # Auto-generate code jika belum ada
        if not self.code:
            self.code = generate_promo_code(
                self.category,
                self.discount_percentage,
                self.start_date
            )
        super().save(*args, **kwargs)
    
    @property
    def remaining_uses(self):
        """Sisa penggunaan promo"""
        return self.max_uses - self.current_uses
    
    @property
    def is_available(self):
        """Check apakah promo masih bisa digunakan"""
        now = timezone.now()
        return (
            self.is_active and
            self.start_date <= now <= self.end_date and
            self.current_uses < self.max_uses
        )
    
    @property
    def status_label(self):
        """Label status promo"""
        now = timezone.now()
        if not self.is_active:
            return "Non-Aktif"
        elif now < self.start_date:
            return "Belum Dimulai"
        elif now > self.end_date:
            return "Sudah Berakhir"
        elif self.current_uses >= self.max_uses:
            return "Kuota Habis"
        else:
            return "Aktif"
    
    def use_promo(self, user, order):
        """
        Method untuk menggunakan promo
        Returns: (success: bool, message: str)
        """
        # Validasi
        if not self.is_available:
            return False, "Promo tidak tersedia"
        
        if self.current_uses >= self.max_uses:
            return False, "Kuota promo sudah habis"
        
        # Increment usage
        self.current_uses += 1
        self.save()
        
        # Create usage record
        PromoUsage.objects.create(
            promo=self,
            user=user,
            order=order
        )
        
        return True, "Promo berhasil digunakan"


class PromoUsage(models.Model):
    """Model untuk tracking penggunaan promo oleh user"""
    promo = models.ForeignKey(
        Promo, 
        on_delete=models.CASCADE,
        related_name='usages'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='promo_usages'
    )
    # order = models.ForeignKey(
    #     'orders.Order',  # Sesuaikan dengan nama app order Anda
    #     on_delete=models.CASCADE,
    #     related_name='promo_usage',
    #     null=True,
    #     blank=True
    # )
    used_at = models.DateTimeField(auto_now_add=True)
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Jumlah diskon yang didapat (dalam Rupiah)"
    )
    
    class Meta:
        ordering = ['-used_at']
        verbose_name = "Penggunaan Promo"
        verbose_name_plural = "Penggunaan Promo"
    
    def __str__(self):
        return f"{self.promo.code} - {self.user.username} - {self.used_at.strftime('%d/%m/%Y')}"