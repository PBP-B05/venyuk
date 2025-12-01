from django.urls import path
from .views import show_matches, create_match, show_match_detail, edit_match, delete_match, join_match, kick_participant

app_name = 'match_up'

urlpatterns = [
    path('', show_matches, name='show_matches'),
    path('create/', create_match, name='create_match'),
    path('detail/<int:id>/', show_match_detail, name='show_match_detail'),
    path('edit/<int:id>/', edit_match, name='edit_match'),
    path('delete/<int:id>/', delete_match, name='delete_match'),
    path('<int:id>/join/', join_match, name='join_match'),
    path('<int:id>/kick/<int:p_id>/', kick_participant, name='kick_participant'),
]
