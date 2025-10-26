from django.urls import path
from . import views

app_name = "versus"

urlpatterns = [
    path("", views.list_challenges, name="list"),
    path("create/", views.create_challenge, name="create"),
    path("<int:pk>/", views.challenge_detail, name="detail"),
    path("<int:pk>/join/", views.join_challenge, name="join"),

    # AJAX / JSON
    path("api/challenges/", views.api_challenge_list, name="api_list"),
    path("api/challenges/<int:pk>/", views.api_challenge_detail, name="api_detail"),
    path("api/challenges/<int:pk>/join/", views.api_join_challenge, name="api_join"),
]
