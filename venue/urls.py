from django.urls import path
from .views import home_section, book_venue, get_venues_json, get_venue_by_id, landing_page, cancel_booking, my_bookings

app_name = 'venue'

urlpatterns = [
    path('', landing_page, name='landing_page'),
    path('home/', home_section, name='home_section'),
    path('book/<uuid:venue_id>/', book_venue, name='book_venue'),
    path('my-bookings/', my_bookings, name='my_bookings'),
    path('cancel-booking/<uuid:booking_id>/', cancel_booking, name='cancel_booking'),
    path('api/venues/', get_venues_json, name='get_venues_json'),
    path('api/venues/<uuid:id>/', get_venue_by_id, name='get_venue_by_id'),
]