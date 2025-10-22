from django.urls import path
from .views import home_section, book_venue, get_venues_json, get_venue_by_id

urlpatterns = [
    path('', home_section, name='home'),
]