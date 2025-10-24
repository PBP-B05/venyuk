from django.db import models
import uuid
from django.conf import settings
from django.contrib.postgres.fields import ArrayField

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
    category = models.TextField(blank=True)  # Menyimpan sebagai CSV: "padel,tennis,badminton"
    address = models.TextField(blank=True)
    thumbnail = models.ImageField(upload_to='venues/', blank=True, null=True)
    rating = models.FloatField(default=0.0)
    price = models.IntegerField(default=0)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def get_categories_list(self):
        """Return categories as list"""
        if self.category:
            return [cat.strip() for cat in self.category.split(',')]
        return []
    
    def get_categories_display(self):
        """Return formatted categories string"""
        categories = self.get_categories_list()
        return ", ".join([dict(self.CATEGORY_CHOICES).get(cat, cat) for cat in categories])
    
    def get_categories_display_list(self):
        """Return categories as list with display names"""
        categories = self.get_categories_list()
        return [dict(self.CATEGORY_CHOICES).get(cat, cat) for cat in categories]
    
    def set_categories(self, categories_list):
        """Set categories from list"""
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