from django.urls import path
from promo import views

app_name = 'promo'

urlpatterns = [
    # CRUD Promo
    path('', views.promo_list, name='list'),
    path('create/', views.create_promo, name='create'),
    path('<int:promo_id>/', views.promo_detail, name='detail'),
    path('<int:promo_id>/update/', views.update_promo, name='update'),
    path('<int:promo_id>/delete/', views.delete_promo, name='delete'),
    
    # Apply Promo (untuk checkout)
    path('apply/', views.apply_promo, name='apply'),
    path('remove/', views.remove_promo, name='remove'),
    path('validate/', views.validate_promo, name='validate'),
    
    # # Usage History
    # path('<int:promo_id>/history/', views.promo_usage_history, name='usage_history'),
    # path('my-usages/', views.my_promo_usages, name='my_usages'),
]