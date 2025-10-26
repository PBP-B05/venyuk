from django.urls import path
from . import views

# Penting: set app_name agar URL namespacing berfungsi
app_name = 'promo'

urlpatterns = [
    path('', views.PromoListView.as_view(), name='promo_list'),
    path('create/', views.PromoCreateView.as_view(), name='promo_create'),
    path('detail/<str:code>/', views.PromoDetailView.as_view(), name='promo_detail'),
    path('edit/<str:code>/', views.PromoUpdateView.as_view(), name='promo_update'),
    path('<str:code>/delete/', views.PromoDeleteView.as_view(), name='promo_delete'),
]
