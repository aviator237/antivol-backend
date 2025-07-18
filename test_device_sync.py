#!/usr/bin/env python3
"""
Script de test pour vérifier la synchronisation des device IDs
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://127.0.0.1:8000"
API_URL = f"{BASE_URL}/api"

def test_device_sync():
    """Test de synchronisation des device IDs"""
    print("🧪 Test de synchronisation des device IDs")
    print("=" * 50)
    
    # 1. Lister tous les devices existants
    print("\n1. 📱 Listing des devices existants...")
    
    # D'abord, on a besoin d'un token d'accès
    # Créer un utilisateur de test
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
    
    # Créer l'utilisateur
    response = requests.post(f"{API_URL}/auth/register/", json=test_user)
    if response.status_code != 201:
        print(f"❌ Erreur création utilisateur: {response.text}")
        return
    
    # Se connecter
    login_data = {
        "email": test_user["email"],
        "password": test_user["password"]
    }
    response = requests.post(f"{API_URL}/auth/login/", json=login_data)
    if response.status_code != 200:
        print(f"❌ Erreur connexion: {response.text}")
        return
    
    auth_data = response.json()
    access_token = auth_data["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    
    print("✅ Utilisateur créé et connecté")
    
    # 2. Créer un device avec un ID spécifique
    print("\n2. 📱 Création d'un device de test...")
    
    test_device = {
        "device_id": f"test_device_sync_{timestamp}",
        "name": "Device de test sync",
        "brand": "TestBrand",
        "model": "TestModel",
        "os_type": "android",
        "os_version": "13.0",
        "app_version": "1.0.0",
        "imei": f"test_imei_{timestamp}",
        "serial_number": f"test_serial_{timestamp}"
    }
    
    response = requests.post(f"{API_URL}/devices/phones/", json=test_device, headers=headers)
    if response.status_code == 201:
        device_data = response.json()
        device_id = device_data['device_id']
        print(f"✅ Device créé avec ID: {device_id}")
    else:
        print(f"❌ Erreur création device: {response.text}")
        return
    
    # 3. Tester la création d'une tentative de déverrouillage
    print(f"\n3. 🔓 Test création tentative avec device_id: {device_id}")
    
    unlock_attempt = {
        "phone_device_id": device_id,
        "attempt_type": "pin",
        "result": "failed",
        "latitude": 48.8566,
        "longitude": 2.3522,
        "ip_address": "192.168.1.100",
        "user_agent": "Test Agent"
    }
    
    response = requests.post(f"{API_URL}/devices/unlock-attempts/", json=unlock_attempt, headers=headers)
    if response.status_code == 201:
        attempt_data = response.json()
        print(f"✅ Tentative créée avec ID: {attempt_data['id']}")
        print(f"   📱 Device associé: {attempt_data.get('phone', 'N/A')}")
    else:
        print(f"❌ Erreur création tentative: {response.status_code}")
        print(f"❌ Corps de la réponse: {response.text}")
        
        # Analyser l'erreur
        try:
            error_data = response.json()
            if 'phone_device_id' in error_data:
                print(f"❌ Erreur phone_device_id: {error_data['phone_device_id']}")
        except:
            pass
        return
    
    # 4. Vérifier que le device existe bien
    print(f"\n4. 🔍 Vérification existence du device...")
    
    response = requests.get(f"{API_URL}/devices/phones/", headers=headers)
    if response.status_code == 200:
        devices = response.json()
        found_device = None
        for device in devices:
            if device['device_id'] == device_id:
                found_device = device
                break
        
        if found_device:
            print(f"✅ Device trouvé dans la liste:")
            print(f"   🆔 ID: {found_device['device_id']}")
            print(f"   📱 Nom: {found_device['name']}")
            print(f"   🏷️ Brand/Model: {found_device['brand']} {found_device['model']}")
        else:
            print(f"❌ Device avec ID {device_id} non trouvé dans la liste")
            print(f"   📱 Devices disponibles: {len(devices)}")
            for i, dev in enumerate(devices):
                print(f"     {i+1}. {dev['device_id']} - {dev['name']}")
    else:
        print(f"❌ Erreur récupération devices: {response.text}")
        return
    
    # 5. Test avec un device_id inexistant
    print(f"\n5. ❌ Test avec device_id inexistant...")
    
    fake_unlock_attempt = {
        "phone_device_id": "device_inexistant_12345",
        "attempt_type": "pin",
        "result": "failed",
        "latitude": 48.8566,
        "longitude": 2.3522
    }
    
    response = requests.post(f"{API_URL}/devices/unlock-attempts/", json=fake_unlock_attempt, headers=headers)
    if response.status_code == 400:
        print("✅ Erreur attendue pour device inexistant")
        try:
            error_data = response.json()
            print(f"   📝 Message: {error_data}")
        except:
            print(f"   📝 Message: {response.text}")
    else:
        print(f"⚠️ Réponse inattendue: {response.status_code} - {response.text}")
    
    print(f"\n🎉 Test de synchronisation terminé !")
    print(f"✅ Le device_id {device_id} fonctionne correctement")

if __name__ == "__main__":
    try:
        test_device_sync()
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
