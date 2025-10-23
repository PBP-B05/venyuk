from django.urls import path
from .views import *

app_name = 'promo'

urlpatterns = [
    path('', show_promos, name='show_promos'),
]