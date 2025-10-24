from django.urls import path
from . import views

# Penting: set app_name agar URL namespacing berfungsi
app_name = 'promo'

urlpatterns = [
    # cth: /promo/
    path('', views.PromoListView.as_view(), name='promo-list'),
    
    # cth: /promo/buat/
    path('create/', views.PromoCreateView.as_view(), name='promo-create'),
    
    # cth: /promo/detail/5/ (pk = 5)
    path('detail/<int:pk>/', views.PromoDetailView.as_view(), name='promo-detail'),
    
    # cth: /promo/edit/5/ (pk = 5)
    path('edit/<int:pk>/', views.PromoUpdateView.as_view(), name='promo-update'),
]
