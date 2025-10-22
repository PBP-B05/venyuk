from django.urls import path
from .views import home_section, book_venue, get_venues_json, get_venue_by_id

urlpatterns = [
    path('', home_section, name='home'),
    path('book-venue/<int:venue_id>/', book_venue, name='book_venue'),
    path('venues/json/', get_venues_json, name='get_venues_json'),
    path('venue/<int:venue_id>/json/', get_venue_by_id, name='get_venue_by_id'),
]