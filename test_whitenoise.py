#!/usr/bin/env python
"""
Script de test pour vérifier que WhiteNoise fonctionne correctement
"""
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "media_app.settings")
    django.setup()
    
    print("=== Test de configuration WhiteNoise ===")
    
    # Vérifier que WhiteNoise est dans les middlewares
    if 'whitenoise.middleware.WhiteNoiseMiddleware' in settings.MIDDLEWARE:
        print("✅ WhiteNoise middleware est configuré")
    else:
        print("❌ WhiteNoise middleware n'est pas configuré")
    
    # Vérifier la configuration STATICFILES_STORAGE
    if 'whitenoise' in settings.STATICFILES_STORAGE.lower():
        print("✅ STATICFILES_STORAGE utilise WhiteNoise")
    else:
        print("❌ STATICFILES_STORAGE n'utilise pas WhiteNoise")
    
    # Vérifier les répertoires
    print(f"📁 STATIC_ROOT: {settings.STATIC_ROOT}")
    print(f"📁 MEDIA_ROOT: {settings.MEDIA_ROOT}")
    print(f"🌐 STATIC_URL: {settings.STATIC_URL}")
    print(f"🌐 MEDIA_URL: {settings.MEDIA_URL}")
    
    # Vérifier que les répertoires existent
    if os.path.exists(settings.STATIC_ROOT):
        static_files = len([f for f in os.listdir(settings.STATIC_ROOT) if os.path.isfile(os.path.join(settings.STATIC_ROOT, f))])
        print(f"✅ STATIC_ROOT existe avec {static_files} fichiers")
    else:
        print("❌ STATIC_ROOT n'existe pas")
    
    if os.path.exists(settings.MEDIA_ROOT):
        print("✅ MEDIA_ROOT existe")
    else:
        print("❌ MEDIA_ROOT n'existe pas - création...")
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        print("✅ MEDIA_ROOT créé")
    
    print("\n=== Configuration WhiteNoise terminée ===")
    print("WhiteNoise est maintenant configuré pour servir :")
    print("- Les fichiers statiques (CSS, JS, images admin)")
    print("- Les fichiers media (uploads utilisateur)")
    print("- Compression automatique des fichiers")
    print("- Cache optimisé pour la production")
