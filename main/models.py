# models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('user', 'User'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=20, default='user')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} - {self.role}"
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_regular_user(self):
        return self.role == 'user'
    
    def get_booking_count(self):
        """Jumlah booking yang pernah dibuat user"""
        return self.booking_set.count()
    
    def get_active_bookings(self):
        """Booking yang masih aktif (pending/confirmed)"""
        return self.booking_set.filter(status__in=['pending', 'confirmed'])
    
    def get_booking_history(self):
        """Semua booking history user"""
        return self.booking_set.all().order_by('-created_at')