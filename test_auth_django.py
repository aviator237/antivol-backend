#!/usr/bin/env python3
"""
Script de test Django pour l'authentification
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'media_app.settings')
django.setup()

from django.contrib.auth.models import User
from authentication.models import EmailVerification
from authentication.serializers import UserRegistrationSerializer, UserLoginSerializer
from rest_framework.test import APIClient
from django.test import TestCase
import json

def test_user_creation():
    """Test de création d'utilisateur"""
    print("🧪 Test de création d'utilisateur...")
    
    # Données de test
    user_data = {
        'first_name': 'Jean',
        'last_name': 'Dupont',
        'email': 'jean.test@example.com',
        'phone_number': '+33123456789',
        'password': 'MotDePasseSecurise123!',
        'password_confirm': 'MotDePasseSecurise123!'
    }
    
    # Test du serializer
    serializer = UserRegistrationSerializer(data=user_data)
    if serializer.is_valid():
        user = serializer.save()
        print(f"✅ Utilisateur créé: {user.email}")
        
        # Vérifier que l'EmailVerification a été créé
        try:
            verification = user.email_verification
            print(f"✅ Vérification d'email créée: {verification.verification_token}")
            return user
        except EmailVerification.DoesNotExist:
            print("❌ Vérification d'email non créée")
            return None
    else:
        print(f"❌ Erreurs de validation: {serializer.errors}")
        return None

def test_login():
    """Test de connexion"""
    print("\n🧪 Test de connexion...")
    
    # Créer un utilisateur de test
    user = User.objects.create_user(
        username='test.login@example.com',
        email='test.login@example.com',
        password='MotDePasseSecurise123!',
        first_name='Test',
        last_name='Login'
    )
    
    # Créer la vérification d'email
    EmailVerification.objects.create(user=user)
    
    # Test de connexion
    login_data = {
        'email': 'test.login@example.com',
        'password': 'MotDePasseSecurise123!'
    }
    
    serializer = UserLoginSerializer(data=login_data)
    if serializer.is_valid():
        authenticated_user = serializer.validated_data['user']
        print(f"✅ Connexion réussie: {authenticated_user.email}")
        return authenticated_user
    else:
        print(f"❌ Erreurs de connexion: {serializer.errors}")
        return None

def test_api_endpoints():
    """Test des endpoints API"""
    print("\n🧪 Test des endpoints API...")
    
    client = APIClient()
    
    # Test d'inscription
    registration_data = {
        'first_name': 'API',
        'last_name': 'Test',
        'email': 'api.test@example.com',
        'phone_number': '+33987654321',
        'password': 'MotDePasseSecurise123!',
        'password_confirm': 'MotDePasseSecurise123!'
    }
    
    response = client.post('/api/auth/register/', registration_data, format='json')
    print(f"Inscription - Status: {response.status_code}")
    if response.status_code == 201:
        print(f"✅ Inscription API réussie: {response.data}")
    else:
        print(f"❌ Échec inscription API: {response.data}")
    
    # Test de connexion
    login_data = {
        'email': 'api.test@example.com',
        'password': 'MotDePasseSecurise123!'
    }
    
    response = client.post('/api/auth/login/', login_data, format='json')
    print(f"Connexion - Status: {response.status_code}")
    if response.status_code == 200:
        print(f"✅ Connexion API réussie")
        access_token = response.data.get('access_token')
        
        # Test du profil avec le token
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = client.get('/api/auth/profile/')
        print(f"Profil - Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Récupération profil réussie: {response.data}")
        else:
            print(f"❌ Échec récupération profil: {response.data}")
    else:
        print(f"❌ Échec connexion API: {response.data}")

def cleanup_test_users():
    """Nettoie les utilisateurs de test"""
    print("\n🧹 Nettoyage des utilisateurs de test...")
    test_emails = [
        'jean.test@example.com',
        'test.login@example.com',
        'api.test@example.com'
    ]
    
    for email in test_emails:
        try:
            user = User.objects.get(email=email)
            user.delete()
            print(f"✅ Utilisateur supprimé: {email}")
        except User.DoesNotExist:
            pass

def main():
    print("🚀 Test de l'authentification Django Antivol")
    print("=" * 50)
    
    # Nettoyer d'abord
    cleanup_test_users()
    
    # Tests
    test_user_creation()
    test_login()
    test_api_endpoints()
    
    # Nettoyer après
    cleanup_test_users()
    
    print("\n" + "=" * 50)
    print("🏁 Tests terminés")

if __name__ == "__main__":
    main()
