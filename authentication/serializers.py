from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import EmailVerification
import re

class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer pour l'inscription d'un utilisateur"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    phone_number = serializers.CharField(max_length=20, required=True)
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password', 'password_confirm', 'phone_number')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
        }
    
    def validate_email(self, value):
        """Valide que l'email n'existe pas déjà"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Un utilisateur avec cet email existe déjà.")
        return value
    
    def validate_phone_number(self, value):
        """Valide le format du numéro de téléphone"""
        # Format simple pour les numéros internationaux
        phone_pattern = r'^\+?[1-9]\d{1,14}$'
        if not re.match(phone_pattern, value):
            raise serializers.ValidationError("Format de numéro de téléphone invalide.")
        return value
    
    def validate(self, attrs):
        """Valide que les mots de passe correspondent"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        return attrs
    
    def create(self, validated_data):
        """Crée un nouvel utilisateur"""
        validated_data.pop('password_confirm')
        phone_number = validated_data.pop('phone_number')
        
        # Utilise l'email comme username
        validated_data['username'] = validated_data['email']
        
        user = User.objects.create_user(**validated_data)
        
        # Stocke le numéro de téléphone dans le profil utilisateur (à adapter selon votre modèle)
        # Pour l'instant, on peut l'ajouter dans first_name temporairement ou créer un profil séparé
        
        # Crée l'objet de vérification d'email
        EmailVerification.objects.create(user=user)
        
        return user

class UserLoginSerializer(serializers.Serializer):
    """Serializer pour la connexion d'un utilisateur"""
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            # Trouve l'utilisateur par email
            try:
                user = User.objects.get(email=email)
                username = user.username
            except User.DoesNotExist:
                raise serializers.ValidationError("Email ou mot de passe incorrect.")
            
            # Authentifie avec le username
            user = authenticate(username=username, password=password)
            
            if not user:
                raise serializers.ValidationError("Email ou mot de passe incorrect.")
            
            if not user.is_active:
                raise serializers.ValidationError("Ce compte est désactivé.")
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError("L'email et le mot de passe sont requis.")

class EmailVerificationSerializer(serializers.Serializer):
    """Serializer pour la vérification d'email"""
    token = serializers.UUIDField(required=False)
    code = serializers.CharField(max_length=6, required=False)

    def validate(self, attrs):
        """Valide le token ou le code de vérification"""
        token = attrs.get('token')
        code = attrs.get('code')

        if not token and not code:
            raise serializers.ValidationError("Le token ou le code de vérification est requis.")

        verification = None

        # Vérification par token (lien email)
        if token:
            try:
                verification = EmailVerification.objects.get(verification_token=token)
            except EmailVerification.DoesNotExist:
                raise serializers.ValidationError("Token de vérification invalide.")

        # Vérification par code (saisie manuelle)
        elif code:
            try:
                verification = EmailVerification.objects.get(verification_code=code)
            except EmailVerification.DoesNotExist:
                raise serializers.ValidationError("Code de vérification invalide.")

        if verification and verification.is_verified:
            raise serializers.ValidationError("Cet email a déjà été vérifié.")

        attrs['verification'] = verification
        return attrs

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer pour le profil utilisateur"""
    email_verified = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'email_verified', 'date_joined')
        read_only_fields = ('id', 'email', 'date_joined')
    
    def get_email_verified(self, obj):
        """Retourne le statut de vérification de l'email"""
        try:
            return obj.email_verification.is_verified
        except EmailVerification.DoesNotExist:
            return False
