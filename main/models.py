from django.contrib.auth.models import User  # pakai User bawaan Django
from django.db import models
import uuid

class CustomUser(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('user', 'User'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

    def is_admin(self):
        return self.role == 'admin'

    def is_regular_user(self):
        return self.role == 'user'

    def get_booking_count(self):
        """Jumlah booking yang pernah dibuat user"""
        return self.user.booking_set.count()

    def get_active_bookings(self):
        """Booking yang masih aktif (pending/confirmed)"""
        return self.user.booking_set.filter(status__in=['pending', 'confirmed'])

    def get_booking_history(self):
        """Semua booking history user"""
        return self.user.booking_set.all().order_by('-created_at')
