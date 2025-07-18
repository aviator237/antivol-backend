"""
WSGI config for media_app project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from media_app.whitenoise_config import MediaWhiteNoise

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'media_app.settings')

application = get_wsgi_application()

# Envelopper l'application avec WhiteNoise pour servir les fichiers statiques et media
application = MediaWhiteNoise(application)
