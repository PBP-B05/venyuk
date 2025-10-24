from django.urls import path
from . import views

app_name = 'authenticate'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('user-data/', views.get_user_data, name='get_user_data'),
    
]