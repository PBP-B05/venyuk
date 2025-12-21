from django.urls import path
from . import views

app_name = 'versus'

urlpatterns = [
    # WEB
    path("", views.list_challenges, name="list"),
    path("create/", views.create_challenge, name="create"),
    path("<int:pk>/", views.challenge_detail, name="detail"),
    path("<int:pk>/edit/", views.update_challenge, name="update"),
    path("<int:pk>/delete/", views.delete_challenge, name="delete"),
    path("<int:pk>/join/", views.join_challenge, name="join"),

    path("communities/", views.community_list, name="community_list"),
    path("communities/create/", views.create_community, name="community_create"),
    path("communities/<int:pk>/", views.community_detail, name="community_detail"),
    path("communities/<int:pk>/edit/", views.update_community, name="community_update"),
    path("communities/<int:pk>/delete/", views.delete_community, name="community_delete"),
    path("communities/<int:pk>/join/", views.join_community, name="community_join"),
    path("communities/leave/", views.leave_community, name="community_leave"),

    # API CHALLENGE
    path("api/challenges/", views.api_challenge_list, name="api_list"),
    path("api/challenges/<int:pk>/", views.api_challenge_detail, name="api_detail"),
    path("api/challenges/<int:pk>/join/", views.api_join_challenge, name="api_join"),
    path("api/challenges/<int:pk>/leave/", views.api_leave_challenge, name="api_leave"),
    path("api/challenges/create/", views.api_create_challenge, name="api_create"),
    path("api/challenges/<int:pk>/update/", views.api_update_challenge, name="api_update"),
    path("api/challenges/<int:pk>/delete/", views.api_delete_challenge, name="api_delete"),

    # API COMMUNITY
    path("api/communities/", views.api_community_list, name="api_community_list"),
    path("api/communities/<int:pk>/", views.api_community_detail, name="api_community_detail"),
    path("api/communities/create/", views.api_community_create, name="api_community_create"),
    path("api/communities/<int:pk>/update/", views.api_community_update, name="api_community_update"),
    path("api/communities/<int:pk>/delete/", views.api_community_delete, name="api_community_delete"),
    path("api/communities/<int:pk>/join/", views.api_community_join, name="api_community_join"),
    path("api/communities/leave/", views.api_community_leave, name="api_community_leave"),
]



