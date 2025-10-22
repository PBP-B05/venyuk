import uuid
from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Promo(models.Model):
    title = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    remaining_uses = models.IntegerField()

    def __str__(self):
        return self.title