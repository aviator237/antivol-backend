from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'authentication'

urlpatterns = [
    # Inscription
    path('register/', views.RegisterView.as_view(), name='register'),
    
    # Connexion
    path('login/', views.login_view, name='login'),
    
    # Vérification d'email
    path('verify-email/', views.verify_email_view, name='verify_email'),
    path('resend-verification/', views.resend_verification_email, name='resend_verification'),
    
    # Profil utilisateur
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    
    # Refresh token
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
