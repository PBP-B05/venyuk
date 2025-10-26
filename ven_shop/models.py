import uuid
from django.db import models
from django.contrib.auth.models import User


class Product(models.Model):
    CATEGORY_CHOICES = [
        ("badminton", "Badminton"),
        ("basketball", "Basketball"),
        ("tennis", "Tennis"),
        ("football", "Football"),
        ("swimming", "Swimming"),
        ("running", "Running"),
        ("volleyball", "Volleyball"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    content = models.TextField()
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, default="update"
    )
    thumbnail = models.URLField(blank=True, null=True)
    price = models.IntegerField()
    rating = models.FloatField(default=0.0)
    stock = models.IntegerField()
    reviewer = models.CharField(max_length=255, null=True, blank=True)
    brand = models.CharField(max_length=100, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.title
    
class Purchased_Product(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    purchase_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.title}"