from django.urls import path
from . import views

app_name = 'devices'

urlpatterns = [
    # Gestion des téléphones
    path('phones/', views.PhoneListCreateView.as_view(), name='phone_list_create'),
    path('phones/<int:pk>/', views.PhoneDetailView.as_view(), name='phone_detail'),
    path('phones/<int:phone_id>/stats/', views.phone_stats_view, name='phone_stats'),
    path('phones/heartbeat/', views.phone_heartbeat_view, name='phone_heartbeat'),
    
    # Tentatives de déverrouillage
    path('unlock-attempts/', views.UnlockAttemptListCreateView.as_view(), name='unlock_attempt_list_create'),
    
    # Photos d'intrusion
    path('intrusion-photos/', views.IntrusionPhotoListCreateView.as_view(), name='intrusion_photo_list_create'),
    
    # Résumé utilisateur
    path('summary/', views.user_devices_summary_view, name='user_devices_summary'),
]
