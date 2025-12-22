from django.urls import path
from . import views

app_name = 'authenticate'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('user-data/', views.get_user_data, name='get_user_data'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('login-flutter/', views.login_flutter, name='login_flutter'),
    path('register-flutter/', views.register_flutter, name='register_flutter'),
    # ===== API (FLUTTER) =====
    path('login_api/', views.login_api, name='login_api'),
    path('register_api/', views.register_api, name='register_api'),
    path('logout_api/', views.logout_user_api, name='logout_api'),
]