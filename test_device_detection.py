#!/usr/bin/env python3
"""
Script de test pour vérifier la détection automatique de device
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://127.0.0.1:8000"
API_URL = f"{BASE_URL}/api"

# Données de test
timestamp = int(time.time())
test_user = {
    "username": f"testuser_{timestamp}",
    "email": f"test_{timestamp}@example.com",
    "password": "testpassword123",
    "password_confirm": "testpassword123",
    "first_name": "Test",
    "last_name": "User",
    "phone_number": "+33123456789"
}

# Simuler différents devices
device_1 = {
    "device_id": f"device_android_123_{timestamp}",
    "name": "Samsung Galaxy S21",
    "brand": "Samsung",
    "model": "Galaxy S21",
    "os_type": "android",
    "os_version": "12.0",
    "app_version": "1.0.0",
    "imei": "123456789012345",
    "serial_number": "SN123456789"
}

device_2 = {
    "device_id": f"device_android_456_{timestamp}",
    "name": "Google Pixel 6",
    "brand": "Google",
    "model": "Pixel 6",
    "os_type": "android",
    "os_version": "13.0",
    "app_version": "1.0.0",
    "imei": "987654321098765",
    "serial_number": "SN987654321"
}

# Device actuel pour les tests de détection
current_device_same_imei = {
    "brand": "Samsung",
    "model": "Galaxy S21",
    "os_type": "android",
    "os_version": "12.0",
    "imei": "123456789012345",  # Même IMEI que device_1
    "serial_number": "SN999999999",
    "app_version": "1.0.0"
}

current_device_same_serial = {
    "brand": "Google",
    "model": "Pixel 6",
    "os_type": "android",
    "os_version": "13.0",
    "imei": "111111111111111",
    "serial_number": "SN987654321",  # Même serial que device_2
    "app_version": "1.0.0"
}

current_device_same_specs = {
    "brand": "Samsung",
    "model": "Galaxy S21",
    "os_type": "android",
    "os_version": "12.0",  # Mêmes specs que device_1
    "imei": "555555555555555",
    "serial_number": "SN555555555",
    "app_version": "1.0.0"
}

current_device_new = {
    "brand": "OnePlus",
    "model": "OnePlus 9",
    "os_type": "android",
    "os_version": "11.0",
    "imei": "777777777777777",
    "serial_number": "SN777777777",
    "app_version": "1.0.0"
}

def setup_test_user():
    """Crée un utilisateur de test et se connecte"""
    print("🔧 Configuration de l'utilisateur de test...")
    
    # Créer l'utilisateur
    response = requests.post(f"{API_URL}/auth/register/", json=test_user)
    if response.status_code != 201:
        print(f"❌ Erreur création utilisateur: {response.text}")
        return None
    
    # Se connecter
    login_data = {
        "email": test_user["email"],
        "password": test_user["password"]
    }
    response = requests.post(f"{API_URL}/auth/login/", json=login_data)
    if response.status_code != 200:
        print(f"❌ Erreur connexion: {response.text}")
        return None
    
    auth_data = response.json()
    access_token = auth_data["access_token"]
    print("✅ Utilisateur créé et connecté")
    return access_token

def create_test_devices(access_token):
    """Crée des devices de test"""
    print("\n📱 Création des devices de test...")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Créer device 1
    response = requests.post(f"{API_URL}/devices/phones/", json=device_1, headers=headers)
    if response.status_code == 201:
        print(f"✅ Device 1 créé: {device_1['name']}")
    else:
        print(f"❌ Erreur device 1: {response.text}")
    
    # Créer device 2
    response = requests.post(f"{API_URL}/devices/phones/", json=device_2, headers=headers)
    if response.status_code == 201:
        print(f"✅ Device 2 créé: {device_2['name']}")
    else:
        print(f"❌ Erreur device 2: {response.text}")

def test_device_detection(access_token, current_device, test_name):
    """Teste la détection automatique avec un device donné"""
    print(f"\n🔍 Test: {test_name}")
    print(f"   Device: {current_device['brand']} {current_device['model']}")
    print(f"   IMEI: {current_device.get('imei', 'N/A')}")
    print(f"   Serial: {current_device.get('serial_number', 'N/A')}")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(f"{API_URL}/devices/phones/detect/", json=current_device, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        action = result.get('action')
        message = result.get('message', '')
        match_method = result.get('match_method', 'N/A')
        
        print(f"   ✅ Action: {action}")
        print(f"   📝 Message: {message}")
        if match_method != 'N/A':
            print(f"   🎯 Méthode de correspondance: {match_method}")
        
        if action == 'found_existing':
            device = result.get('device', {})
            print(f"   📱 Device trouvé: {device.get('name', 'N/A')} (ID: {device.get('device_id', 'N/A')})")
        elif action == 'need_selection':
            devices = result.get('devices', [])
            print(f"   📱 Devices disponibles: {len(devices)}")
        
        return True
    else:
        print(f"   ❌ Erreur: {response.status_code} - {response.text}")
        return False

def main():
    """Fonction principale de test"""
    print("🧪 Test de détection automatique de device")
    print("=" * 50)
    
    # Configuration
    access_token = setup_test_user()
    if not access_token:
        return
    
    # Créer des devices de test
    create_test_devices(access_token)
    
    # Tests de détection
    tests = [
        (current_device_same_imei, "Détection par IMEI identique"),
        (current_device_same_serial, "Détection par numéro de série identique"),
        (current_device_same_specs, "Détection par caractéristiques techniques"),
        (current_device_new, "Nouveau device (sélection manuelle)"),
    ]
    
    success_count = 0
    for device, test_name in tests:
        if test_device_detection(access_token, device, test_name):
            success_count += 1
    
    print(f"\n📊 Résultats: {success_count}/{len(tests)} tests réussis")
    
    if success_count == len(tests):
        print("🎉 Tous les tests de détection automatique ont réussi !")
    else:
        print("⚠️ Certains tests ont échoué")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
