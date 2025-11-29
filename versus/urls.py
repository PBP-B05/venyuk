from django.urls import path
from . import views

app_name = "versus"

urlpatterns = [
    path("", views.list_challenges, name="list"),
    path("create/", views.create_challenge, name="create"),
    path("<int:pk>/", views.challenge_detail, name="detail"),
    path("<int:pk>/edit/", views.update_challenge, name="update"),
    path("<int:pk>/delete/", views.delete_challenge, name="delete"),
    path("<int:pk>/join/", views.join_challenge, name="join"),

    path("api/challenges/", views.api_challenge_list, name="api_list"),
    path("api/challenges/<int:pk>/", views.api_challenge_detail, name="api_detail"),
    path("api/challenges/<int:pk>/join/", views.api_join_challenge, name="api_join"),

    path("communities/", views.community_list, name="community_list"),
    path("communities/create/", views.create_community, name="community_create"),
    path("communities/<int:pk>/", views.community_detail, name="community_detail"),
    path("communities/<int:pk>/edit/", views.update_community, name="community_update"),
    path("communities/<int:pk>/delete/", views.delete_community, name="community_delete"),

    path("communities/<int:pk>/join/", views.join_community, name="community_join"),
    path("communities/leave/", views.leave_community, name="community_leave"),
]





