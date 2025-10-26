from django.db import models
import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from datetime import datetime, date, time
from django.contrib.auth.models import User
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

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

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    category = models.TextField(blank=True)
    address = models.TextField(blank=True)
    thumbnail = models.ImageField(upload_to='venues/', blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)  # TAMBAH FIELD INI
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
    
    def get_image_url(self):
        """Return image URL, prefer thumbnail if exists, otherwise use image_url"""
        if self.thumbnail and self.thumbnail.url:
            return self.thumbnail.url
        elif self.image_url:
            return self.image_url
        return None
    
    def clean(self):
        """Custom validation for the model"""
        if self.image_url:
            validator = URLValidator()
            try:
                validator(self.image_url)
            except ValidationError:
                raise ValidationError({'image_url': 'Enter a valid URL.'})
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE)
    booking_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['venue', 'booking_date', 'status']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.venue.name} - {self.booking_date}"

    def get_duration_hours(self):
        """Calculate duration in hours"""
        start_dt = datetime.combine(date.today(), self.start_time)
        end_dt = datetime.combine(date.today(), self.end_time)
        duration = end_dt - start_dt
        return duration.seconds // 3600

    def is_editable(self):
        """Check if booking can be edited"""
        today = date.today()
        if self.booking_date < today:
            return False
        
        if self.status not in ['pending', 'confirmed']:
            return False
        
        # If booking is today, check if start time hasn't passed
        if self.booking_date == today:
            now = datetime.now().time()
            if self.start_time <= now:
                return False
        
        return True

    def has_time_conflict(self, other_booking):
        """Check if this booking conflicts with another booking"""
        if self.venue != other_booking.venue:
            return False
        
        if self.booking_date != other_booking.booking_date:
            return False
        
        # Check for time overlap
        return (self.start_time < other_booking.end_time and 
                self.end_time > other_booking.start_time)
    
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