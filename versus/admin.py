# versus/admin.py
from django.contrib import admin
from .models import Community, Challenge

@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ("name", "primary_sport", "owner")
    search_fields = ("name",)
    list_filter = ("primary_sport",)

@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ("title", "sport", "host", "start_at", "status", "cost_per_person")
    search_fields = ("title",)
    list_filter = ("sport", "status", "start_at")
    autocomplete_fields = ("host", "opponent")
