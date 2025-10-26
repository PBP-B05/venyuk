from django.db import models
from django.contrib.auth.models import User
import uuid

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    alamat = models.TextField(blank=True, null=True)
    no_telepon = models.CharField(max_length=20, blank=True, null=True)

    profile_pic = models.ImageField(
        upload_to='profile_pics/', 
        null=True, 
        blank=True, 
        default='profile_pics/default.jpg'
    )

    def __str__(self):
        return self.user.username