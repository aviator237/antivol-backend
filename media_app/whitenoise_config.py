"""
Configuration personnalisée pour WhiteNoise afin de servir les fichiers media
"""
from whitenoise import WhiteNoise
from django.conf import settings
import os


class MediaWhiteNoise(WhiteNoise):
    """
    Extension de WhiteNoise pour servir les fichiers media en plus des fichiers statiques
    """
    
    def __init__(self, application, **kwargs):
        super().__init__(application, **kwargs)
        
        # Ajouter le répertoire media aux répertoires servis par WhiteNoise
        if hasattr(settings, 'MEDIA_ROOT') and hasattr(settings, 'MEDIA_URL'):
            media_root = settings.MEDIA_ROOT
            media_url = settings.MEDIA_URL.rstrip('/')
            
            if os.path.exists(media_root):
                self.add_files(media_root, prefix=media_url)
