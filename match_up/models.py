from django.db import models
from venue.models import Venue
from django.contrib.auth.models import User
    
class Match(models.Model):
    
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE) 
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    
    slot_total = models.IntegerField(default=0)
    slot_terisi = models.IntegerField(default=0)
    
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    
    difficulty_level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')

    def __str__(self):
        return f"Match at {self.venue.name} on {self.start_time.strftime('%d %b %Y')}"