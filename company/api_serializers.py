from rest_framework import serializers
from .models import Company, Category, Catalog, PublicService


class PublicServiceSerializer(serializers.ModelSerializer):
    """Sérialiseur pour le modèle PublicService"""
    service_type_display = serializers.CharField(source='get_service_type_display', read_only=True)
    full_address = serializers.CharField(source='get_full_address', read_only=True)
    google_maps_url = serializers.CharField(source='get_google_maps_url', read_only=True)
    
    class Meta:
        model = PublicService
        fields = [
            'id', 'name', 'service_type', 'service_type_display', 
            'address', 'postal_code', 'city', 'full_address',
            'latitude', 'longitude', 'google_maps_url',
            'phone', 'email', 'website',
            'opening_hour', 'closing_hour', 'notes'
        ]
