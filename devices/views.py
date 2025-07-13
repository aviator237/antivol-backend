from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count, Q
from .models import Phone, UnlockAttempt, IntrusionPhoto
from .serializers import (
    PhoneSerializer, PhoneRegistrationSerializer, UnlockAttemptSerializer,
    UnlockAttemptCreateSerializer, IntrusionPhotoSerializer,
    IntrusionPhotoUploadSerializer, PhoneStatsSerializer,
    UserDevicesSummarySerializer
)

class PhoneListCreateView(generics.ListCreateAPIView):
    """Vue pour lister et créer des téléphones"""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PhoneRegistrationSerializer
        return PhoneSerializer

    def get_queryset(self):
        return Phone.objects.filter(user=self.request.user)

class PhoneDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vue pour récupérer, modifier ou supprimer un téléphone"""
    serializer_class = PhoneSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Phone.objects.filter(user=self.request.user)

class UnlockAttemptListCreateView(generics.ListCreateAPIView):
    """Vue pour lister et créer des tentatives de déverrouillage"""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UnlockAttemptCreateSerializer
        return UnlockAttemptSerializer

    def get_queryset(self):
        queryset = UnlockAttempt.objects.filter(phone__user=self.request.user)

        # Filtres optionnels
        phone_id = self.request.query_params.get('phone_id')
        if phone_id:
            queryset = queryset.filter(phone_id=phone_id)

        result = self.request.query_params.get('result')
        if result:
            queryset = queryset.filter(result=result)

        suspicious_only = self.request.query_params.get('suspicious_only')
        if suspicious_only == 'true':
            # Filtrer les tentatives suspectes
            queryset = queryset.filter(result='failed')

        return queryset.select_related('phone')

class IntrusionPhotoListCreateView(generics.ListCreateAPIView):
    """Vue pour lister et uploader des photos d'intrusion"""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return IntrusionPhotoUploadSerializer
        return IntrusionPhotoSerializer

    def get_queryset(self):
        queryset = IntrusionPhoto.objects.filter(unlock_attempt__phone__user=self.request.user)

        # Filtres optionnels
        phone_id = self.request.query_params.get('phone_id')
        if phone_id:
            queryset = queryset.filter(unlock_attempt__phone_id=phone_id)

        camera_type = self.request.query_params.get('camera_type')
        if camera_type:
            queryset = queryset.filter(camera_type=camera_type)

        return queryset.select_related('unlock_attempt', 'unlock_attempt__phone')

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def phone_stats_view(request, phone_id):
    """Vue pour récupérer les statistiques d'un téléphone"""
    try:
        phone = Phone.objects.get(id=phone_id, user=request.user)
    except Phone.DoesNotExist:
        return Response({
            'error': 'Téléphone non trouvé'
        }, status=status.HTTP_404_NOT_FOUND)

    # Calculer les statistiques
    attempts = phone.unlock_attempts.all()
    photos = IntrusionPhoto.objects.filter(unlock_attempt__phone=phone)

    # Statistiques de base
    total_attempts = attempts.count()
    failed_attempts = attempts.filter(result='failed').count()
    successful_attempts = attempts.filter(result='success').count()

    # Tentatives suspectes
    suspicious_attempts = sum(1 for attempt in attempts if attempt.is_suspicious)

    # Type de tentative le plus courant
    most_common_type = attempts.values('attempt_type').annotate(
        count=Count('attempt_type')
    ).order_by('-count').first()

    most_common_attempt_type = most_common_type['attempt_type'] if most_common_type else 'N/A'

    # Statistiques quotidiennes (7 derniers jours)
    daily_stats = []
    for i in range(7):
        date = timezone.now().date() - timezone.timedelta(days=i)
        day_attempts = attempts.filter(timestamp__date=date)
        daily_stats.append({
            'date': date.isoformat(),
            'total_attempts': day_attempts.count(),
            'failed_attempts': day_attempts.filter(result='failed').count(),
            'photos_count': photos.filter(timestamp__date=date).count()
        })

    stats_data = {
        'total_attempts': total_attempts,
        'failed_attempts': failed_attempts,
        'successful_attempts': successful_attempts,
        'suspicious_attempts': suspicious_attempts,
        'photos_count': photos.count(),
        'last_activity': phone.last_seen,
        'most_common_attempt_type': most_common_attempt_type,
        'daily_stats': daily_stats
    }

    serializer = PhoneStatsSerializer(stats_data)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_devices_summary_view(request):
    """Vue pour récupérer le résumé des appareils de l'utilisateur"""
    user = request.user
    phones = Phone.objects.filter(user=user)

    # Statistiques générales
    total_devices = phones.count()
    active_devices = phones.filter(status='active').count()
    online_devices = sum(1 for phone in phones if phone.is_online)

    # Appareils avec activité récente (24h)
    yesterday = timezone.now() - timezone.timedelta(days=1)
    devices_with_recent_activity = phones.filter(last_seen__gte=yesterday).count()

    # Statistiques globales
    total_unlock_attempts = UnlockAttempt.objects.filter(phone__user=user).count()
    total_photos = IntrusionPhoto.objects.filter(unlock_attempt__phone__user=user).count()

    summary_data = {
        'total_devices': total_devices,
        'active_devices': active_devices,
        'online_devices': online_devices,
        'devices_with_recent_activity': devices_with_recent_activity,
        'total_unlock_attempts': total_unlock_attempts,
        'total_photos': total_photos,
        'devices': phones
    }

    serializer = UserDevicesSummarySerializer(summary_data)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def phone_heartbeat_view(request):
    """Vue pour mettre à jour le statut 'last_seen' d'un téléphone"""
    device_id = request.data.get('device_id')

    if not device_id:
        return Response({
            'error': 'device_id requis'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        phone = Phone.objects.get(device_id=device_id, user=request.user)
        phone.last_seen = timezone.now()
        phone.save(update_fields=['last_seen'])

        return Response({
            'message': 'Heartbeat enregistré',
            'last_seen': phone.last_seen
        })
    except Phone.DoesNotExist:
        return Response({
            'error': 'Téléphone non trouvé'
        }, status=status.HTTP_404_NOT_FOUND)
