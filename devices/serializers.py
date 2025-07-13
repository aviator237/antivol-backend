from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Phone, UnlockAttempt, IntrusionPhoto

class PhoneSerializer(serializers.ModelSerializer):
    """Serializer pour les téléphones"""
    user = serializers.StringRelatedField(read_only=True)
    display_name = serializers.ReadOnlyField()
    is_online = serializers.ReadOnlyField()
    unlock_attempts_count = serializers.SerializerMethodField()
    recent_attempts_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Phone
        fields = [
            'id', 'device_id', 'user', 'name', 'display_name',
            'brand', 'model', 'os_type', 'os_version', 'app_version',
            'status', 'is_primary', 'is_online', 'last_seen',
            'unlock_attempts_threshold', 'photo_capture_enabled', 
            'location_tracking_enabled', 'unlock_attempts_count',
            'recent_attempts_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['device_id', 'user', 'last_seen', 'created_at', 'updated_at']
    
    def get_unlock_attempts_count(self, obj):
        """Retourne le nombre total de tentatives de déverrouillage"""
        return obj.unlock_attempts.count()
    
    def get_recent_attempts_count(self, obj):
        """Retourne le nombre de tentatives récentes (24h)"""
        from django.utils import timezone
        yesterday = timezone.now() - timezone.timedelta(days=1)
        return obj.unlock_attempts.filter(timestamp__gte=yesterday).count()

class PhoneRegistrationSerializer(serializers.ModelSerializer):
    """Serializer pour l'enregistrement d'un nouveau téléphone"""

    class Meta:
        model = Phone
        fields = [
            'id', 'device_id', 'name', 'brand', 'model', 'os_type', 'os_version',
            'app_version', 'imei', 'serial_number', 'is_primary',
            'unlock_attempts_threshold', 'photo_capture_enabled',
            'location_tracking_enabled', 'created_at'
        ]
        read_only_fields = ['id', 'device_id', 'created_at']
    
    def create(self, validated_data):
        """Crée un nouveau téléphone pour l'utilisateur connecté"""
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)

class UnlockAttemptSerializer(serializers.ModelSerializer):
    """Serializer pour les tentatives de déverrouillage"""
    phone_name = serializers.CharField(source='phone.name', read_only=True)
    is_suspicious = serializers.ReadOnlyField()
    photos_count = serializers.SerializerMethodField()
    
    class Meta:
        model = UnlockAttempt
        fields = [
            'id', 'phone', 'phone_name', 'attempt_type', 'result',
            'timestamp', 'latitude', 'longitude', 'location_accuracy',
            'ip_address', 'user_agent', 'is_suspicious', 'photos_count'
        ]
        read_only_fields = ['timestamp']
    
    def get_photos_count(self, obj):
        """Retourne le nombre de photos associées"""
        return obj.photos.count()

class UnlockAttemptCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer une tentative de déverrouillage"""
    phone_device_id = serializers.UUIDField(write_only=True)
    is_suspicious = serializers.ReadOnlyField()

    class Meta:
        model = UnlockAttempt
        fields = [
            'id', 'phone_device_id', 'attempt_type', 'result',
            'latitude', 'longitude', 'location_accuracy',
            'ip_address', 'user_agent', 'is_suspicious', 'timestamp'
        ]
        read_only_fields = ['id', 'is_suspicious', 'timestamp']
    
    def validate_phone_device_id(self, value):
        """Valide que le device_id appartient à l'utilisateur connecté"""
        user = self.context['request'].user
        try:
            phone = Phone.objects.get(device_id=value, user=user)
            return value
        except Phone.DoesNotExist:
            raise serializers.ValidationError("Appareil non trouvé ou non autorisé.")
    
    def create(self, validated_data):
        """Crée une nouvelle tentative de déverrouillage"""
        device_id = validated_data.pop('phone_device_id')
        user = self.context['request'].user
        phone = Phone.objects.get(device_id=device_id, user=user)
        validated_data['phone'] = phone
        return super().create(validated_data)

class IntrusionPhotoSerializer(serializers.ModelSerializer):
    """Serializer pour les photos d'intrusion"""
    unlock_attempt_info = serializers.SerializerMethodField()
    file_size_display = serializers.SerializerMethodField()
    
    class Meta:
        model = IntrusionPhoto
        fields = [
            'id', 'unlock_attempt', 'unlock_attempt_info', 'photo',
            'camera_type', 'file_size', 'file_size_display',
            'timestamp', 'exif_data'
        ]
        read_only_fields = ['file_size', 'timestamp']
    
    def get_unlock_attempt_info(self, obj):
        """Retourne des informations sur la tentative de déverrouillage"""
        return {
            'phone_name': obj.unlock_attempt.phone.name,
            'attempt_type': obj.unlock_attempt.get_attempt_type_display(),
            'result': obj.unlock_attempt.get_result_display(),
            'timestamp': obj.unlock_attempt.timestamp,
            'is_suspicious': obj.unlock_attempt.is_suspicious
        }
    
    def get_file_size_display(self, obj):
        """Retourne la taille du fichier en format lisible"""
        if obj.file_size:
            if obj.file_size < 1024:
                return f"{obj.file_size} B"
            elif obj.file_size < 1024 * 1024:
                return f"{obj.file_size / 1024:.1f} KB"
            else:
                return f"{obj.file_size / (1024 * 1024):.1f} MB"
        return "N/A"

class IntrusionPhotoUploadSerializer(serializers.ModelSerializer):
    """Serializer pour uploader des photos d'intrusion"""
    unlock_attempt_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = IntrusionPhoto
        fields = ['unlock_attempt_id', 'photo', 'camera_type', 'exif_data']
    
    def validate_unlock_attempt_id(self, value):
        """Valide que la tentative appartient à l'utilisateur connecté"""
        user = self.context['request'].user
        try:
            attempt = UnlockAttempt.objects.get(id=value, phone__user=user)
            return value
        except UnlockAttempt.DoesNotExist:
            raise serializers.ValidationError("Tentative de déverrouillage non trouvée ou non autorisée.")
    
    def create(self, validated_data):
        """Crée une nouvelle photo d'intrusion"""
        attempt_id = validated_data.pop('unlock_attempt_id')
        user = self.context['request'].user
        unlock_attempt = UnlockAttempt.objects.get(id=attempt_id, phone__user=user)
        validated_data['unlock_attempt'] = unlock_attempt
        return super().create(validated_data)

class PhoneStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques d'un téléphone"""
    total_attempts = serializers.IntegerField()
    failed_attempts = serializers.IntegerField()
    successful_attempts = serializers.IntegerField()
    suspicious_attempts = serializers.IntegerField()
    photos_count = serializers.IntegerField()
    last_activity = serializers.DateTimeField()
    most_common_attempt_type = serializers.CharField()
    daily_stats = serializers.ListField(child=serializers.DictField())

class UserDevicesSummarySerializer(serializers.Serializer):
    """Serializer pour le résumé des appareils d'un utilisateur"""
    total_devices = serializers.IntegerField()
    active_devices = serializers.IntegerField()
    online_devices = serializers.IntegerField()
    devices_with_recent_activity = serializers.IntegerField()
    total_unlock_attempts = serializers.IntegerField()
    total_photos = serializers.IntegerField()
    devices = PhoneSerializer(many=True)
