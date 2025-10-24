from django.db import models
from django.contrib.auth.models import User
from venue.models import Venue

class Match(models.Model):
    
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    venue = models.ForeignKey(Venue, on_delete=models.SET_NULL, null=True, blank=True)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    slot_total = models.IntegerField(default=0)
    slot_terisi = models.IntegerField(default=0)
    
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    
    difficulty_level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')

    def __str__(self):
        return f"Match on {self.start_time.strftime('%d %b %Y')} by {self.creator.username if self.creator else 'Unknown'}"
    

class Participant(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.match}"
