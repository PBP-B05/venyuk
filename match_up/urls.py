from django.urls import path
from .views import show_matches, create_match, show_match_detail, edit_match, delete_match, join_match, kick_participant, create_match_flutter, show_match_detail_json, join_match_flutter
from .views import edit_match_flutter, kick_participant_flutter, delete_match_flutter, proxy_image

app_name = 'match_up'

urlpatterns = [
    path('', show_matches, name='show_matches'),
    path('create/', create_match, name='create_match'),
    path('detail/<int:id>/', show_match_detail, name='show_match_detail'),
    path('edit/<int:id>/', edit_match, name='edit_match'),
    path('delete/<int:id>/', delete_match, name='delete_match'),
    path('<int:id>/join/', join_match, name='join_match'),
    path('<int:id>/kick/<int:p_id>/', kick_participant, name='kick_participant'),
    path('create-match/', create_match_flutter, name='create_match_flutter'),
    path('<int:id>/json/', show_match_detail_json, name='show_match_detail_json'),
    path('join-flutter/<int:id>/', join_match_flutter, name='join_match_flutter'),
    path('edit-flutter/<int:id>/', edit_match_flutter, name='edit_match_flutter'),
    path('kick-flutter/<int:id>/<int:p_id>/', kick_participant_flutter, name='kick_participant_flutter'),
    path('delete-flutter/<int:id>/', delete_match_flutter, name='delete_match_flutter'),
    path('proxy-image/', proxy_image, name='proxy_image'),
]
