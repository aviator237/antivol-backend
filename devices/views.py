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
import json

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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def device_detection_view(request):
    """
    Endpoint pour la détection automatique de device lors de la connexion.
    Reçoit les informations du device actuel et retourne :
    - La liste des devices existants
    - Un device correspondant s'il est trouvé automatiquement
    - Les informations nécessaires pour la sélection manuelle
    """
    try:
        # Récupérer les informations du device actuel depuis la requête
        device_info = request.data

        # Récupérer tous les devices de l'utilisateur
        user_devices = Phone.objects.filter(user=request.user)
        devices_data = PhoneSerializer(user_devices, many=True).data

        # Essayer de trouver un device correspondant automatiquement
        matching_device = None

        # 1. Recherche par IMEI (le plus fiable)
        if device_info.get('imei') and device_info['imei'].strip():
            matching_device = user_devices.filter(
                imei=device_info['imei'].strip()
            ).first()
            if matching_device:
                return Response({
                    'action': 'found_existing',
                    'device': PhoneSerializer(matching_device).data,
                    'devices': devices_data,
                    'match_method': 'imei',
                    'message': 'Device trouvé par IMEI'
                })

        # 2. Recherche par numéro de série
        if device_info.get('serial_number') and device_info['serial_number'].strip():
            matching_device = user_devices.filter(
                serial_number=device_info['serial_number'].strip()
            ).first()
            if matching_device:
                return Response({
                    'action': 'found_existing',
                    'device': PhoneSerializer(matching_device).data,
                    'devices': devices_data,
                    'match_method': 'serial_number',
                    'message': 'Device trouvé par numéro de série'
                })

        # 3. Recherche par combinaison brand + model + os_version (moins fiable)
        if (device_info.get('brand') and device_info.get('model') and
            device_info.get('os_version')):
            matching_devices = user_devices.filter(
                brand__iexact=device_info['brand'],
                model__iexact=device_info['model'],
                os_version=device_info['os_version']
            )

            # Si un seul device correspond, on peut l'utiliser
            if matching_devices.count() == 1:
                matching_device = matching_devices.first()
                return Response({
                    'action': 'found_existing',
                    'device': PhoneSerializer(matching_device).data,
                    'devices': devices_data,
                    'match_method': 'brand_model_os',
                    'message': 'Device trouvé par caractéristiques techniques'
                })

        # Aucun device correspondant trouvé automatiquement
        if not user_devices.exists():
            # Aucun device enregistré, créer automatiquement
            return Response({
                'action': 'create_new',
                'devices': [],
                'current_device_info': device_info,
                'message': 'Aucun device enregistré, création automatique recommandée'
            })
        else:
            # Plusieurs devices, sélection manuelle requise
            return Response({
                'action': 'need_selection',
                'devices': devices_data,
                'current_device_info': device_info,
                'message': 'Sélection manuelle requise'
            })

    except Exception as e:
        return Response({
            'error': f'Erreur lors de la détection du device: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
