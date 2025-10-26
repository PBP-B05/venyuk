from django.urls import path
from . import views

app_name = 'venue'

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('home/', views.home_section, name='home_section'),
    path('book/<uuid:venue_id>/', views.book_venue, name='book_venue'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('cancel-booking/<uuid:booking_id>/', views.cancel_booking, name='cancel_booking'),  # Pastikan ini ada
    path('availability/<uuid:venue_id>/', views.get_venue_availability, name='get_venue_availability'),
    path('json/', views.get_venues_json, name='venues_json'),
    path('json/<uuid:id>/', views.get_venue_by_id, name='venue_json'),
]