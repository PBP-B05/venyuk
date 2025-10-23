# match_up/urls.py

from django.urls import path
from .views import show_matches, create_match, show_match_detail

app_name = 'match_up' # Pastikan app_name juga konsisten

urlpatterns = [
    path('', show_matches, name='show_matches'),
    path('create/', create_match, name='create_match'), # Ini adalah rute yang dicari
    path('detail/<int:id>/', show_match_detail, name='show_match_detail'),
]