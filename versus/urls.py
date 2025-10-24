# versus/urls.py
from django.urls import path, include
from . import views

app_name = "versus"

urlpatterns = [
    path("", views.list_challenges, name="list"),
    path("create/", views.create_challenge, name="create"),
    path("<int:pk>/", views.challenge_detail, name="detail"),
    path("<int:pk>/join/", views.join_challenge, name="join"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("create/", views.create_challenge, name="create"),
    path("<int:pk>/", views.challenge_detail, name="detail"),
    path("<int:pk>/join/", views.join_challenge, name="join"),
    path("", views.index, name="index"),
    
]
