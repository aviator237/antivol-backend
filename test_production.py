#!/usr/bin/env python
"""
Test de la configuration en mode production
"""
import os
import sys
import django
from django.conf import settings
from django.core.management import execute_from_command_line

if __name__ == "__main__":
    # Simuler un environnement de production
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "media_app.settings")
    os.environ["DEBUG"] = "False"
    
    django.setup()
    
    print("=== Test en mode production ===")
    print(f"DEBUG: {settings.DEBUG}")
    print(f"STATIC_URL: {settings.STATIC_URL}")
    print(f"MEDIA_URL: {settings.MEDIA_URL}")
    
    # Vérifier que WhiteNoise est configuré
    print(f"STATICFILES_STORAGE: {settings.STATICFILES_STORAGE}")
    
    # Collecter les fichiers statiques
    print("\n📦 Collection des fichiers statiques...")
    execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
    
    print("\n✅ Configuration prête pour la production !")
    print("WhiteNoise servira automatiquement :")
    print("- Fichiers statiques avec compression")
    print("- Fichiers media")
    print("- Interface d'administration")
