from django.db import models
import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from datetime import datetime, date, time

class Venue(models.Model):
    CATEGORY_CHOICES = [
        ('sepak bola', 'Sepak Bola'),
        ('futsal', 'Futsal'),
        ('mini soccer', 'Mini Soccer'),
        ('basketball', 'Basketball'),
        ('tennis', 'Tennis'),
        ('badminton', 'Badminton'),
        ('padel', 'Padel'),
        ('pickle ball', 'Pickle Ball'),
        ('squash', 'Squash'),
        ('voli', 'Voli'),
        ('biliard', 'Biliard'),
        ('golf', 'Golf'),
        ('shooting', 'Shooting'),
        ('tennis meja', 'Tennis Meja'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    category = models.TextField(blank=True)
    address = models.TextField(blank=True)
    thumbnail = models.URLField(blank=True, null=True)
    rating = models.FloatField(default=0.0)
    price = models.IntegerField(default=0)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def get_categories_list(self):
        if self.category:
            return [cat.strip() for cat in self.category.split(',')]
        return []
    
    def get_categories_display(self):
        categories = self.get_categories_list()
        return ", ".join([dict(self.CATEGORY_CHOICES).get(cat, cat) for cat in categories])
    
    def get_categories_display_list(self):
        categories = self.get_categories_list()
        return [dict(self.CATEGORY_CHOICES).get(cat, cat) for cat in categories]
    
    def set_categories(self, categories_list):
        self.category = ",".join(categories_list)

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE)
    booking_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    total_price = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.venue.name} - {self.booking_date}"
    
    def clean(self):
        """Validasi logika booking"""
        # Validasi waktu selesai harus setelah waktu mulai
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValidationError("Waktu selesai harus setelah waktu mulai")
            
            # Validasi durasi minimal 1 jam
            start_dt = datetime.combine(date.today(), self.start_time)
            end_dt = datetime.combine(date.today(), self.end_time)
            duration_hours = (end_dt - start_dt).seconds / 3600
            if duration_hours < 1:
                raise ValidationError("Durasi booking minimal 1 jam")
        
        # Validasi tanggal booking tidak boleh di masa lalu
        if self.booking_date and self.booking_date < date.today():
            raise ValidationError("Tidak bisa booking untuk tanggal yang sudah lewat")
    
    def save(self, *args, **kwargs):
        """Override save untuk validasi"""
        self.clean()
        super().save(*args, **kwargs)
    
    def get_duration_hours(self):
        """Hitung durasi dalam jam"""
        start_dt = datetime.combine(date.today(), self.start_time)
        end_dt = datetime.combine(date.today(), self.end_time)
        return (end_dt - start_dt).seconds / 3600
    
    def check_availability(self):
        """Cek apakah venue available pada waktu yang diminta"""
        conflicting_bookings = Booking.objects.filter(
            venue=self.venue,
            booking_date=self.booking_date,
            status__in=['pending', 'confirmed'],
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        ).exclude(id=self.id)
        
        return not conflicting_bookings.exists()