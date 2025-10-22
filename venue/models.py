from django.db import models
import uuid

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
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='futsal')
    # capacity = models.IntegerField(default=0)
    address = models.TextField(blank=True)
    thumbnail = models.ImageField(upload_to='venues/', blank=True, null=True)
    rating = models.FloatField(default=0.0)
    price = models.IntegerField(default=0)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name