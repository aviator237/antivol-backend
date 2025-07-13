from rest_framework import serializers
from .models import Category, Company, Catalog, DistributionZone
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']


class CompanySerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Company
        fields = ['id', 'name', 'category', 'address', 'postal_code', 'city', 'siret',
                 'latitude', 'longitude', 'opening_hour', 'closing_hour']


class CompanyLightSerializer(serializers.ModelSerializer):
    """Version allégée du sérialiseur Company pour les listes"""
    class Meta:
        model = Company
        fields = ['id', 'name', 'city', 'latitude', 'longitude', 'opening_hour', 'closing_hour']


class DistributionZoneSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les zones de diffusion"""
    company = CompanyLightSerializer(read_only=True)

    class Meta:
        model = DistributionZone
        fields = ['id', 'name', 'latitude', 'longitude', 'company', 'created_at', 'updated_at']


class DistributionZoneLightSerializer(serializers.ModelSerializer):
    """Version allégée du sérialiseur DistributionZone pour les listes"""
    class Meta:
        model = DistributionZone
        fields = ['id', 'name', 'latitude', 'longitude']


class CatalogSerializer(serializers.ModelSerializer):
    company = CompanyLightSerializer(read_only=True)
    publisher = UserSerializer(read_only=True)
    distribution_zones = DistributionZoneLightSerializer(many=True, read_only=True)

    class Meta:
        model = Catalog
        fields = ['id', 'title', 'file', 'company', 'publisher', 'distribution_zones', 'created_at', 'updated_at']
