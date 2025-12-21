from django.contrib import admin
from .models import Community, Challenge


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ("name", "primary_sport", "owner", "total_members")
    search_fields = ("name", "owner__username", "owner__email")
    list_filter = ("primary_sport",)
    filter_horizontal = ("members",)


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "sport",
        "match_category",
        "host",
        "opponent",
        "status",
        "start_at",
    )
    search_fields = ("title", "host__name", "opponent__name")
    list_filter = ("sport", "match_category", "status")
    raw_id_fields = ("host", "opponent", "venue")