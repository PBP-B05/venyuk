from django.urls import path
from . import views

app_name = 'promo'

urlpatterns = [
    path('api/get_promos/', views.get_promos_json_view, name='get_promos_json'),
    path('create/', views.promo_create_view, name='promo_create'),
    path('', views.promo_list_view, name='promo_list'),
    path('<str:code>/update/', views.promo_update_view, name='promo_update'),
    path('<str:code>/delete/', views.promo_delete_view, name='promo_delete'),
    path('<str:code>/', views.promo_detail_view, name='promo_detail'),
]
