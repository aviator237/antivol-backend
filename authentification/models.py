from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ImproperlyConfigured

class Otp(models.Model):
    user = models.OneToOneField(User, blank=False, null=True, verbose_name='propriétaire', on_delete=models.CASCADE)
    token = models.CharField(verbose_name='OTP', max_length=6, null=False)
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True, verbose_name="date de création")

    def __str__(self):
        return self.token
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "OTP"
        verbose_name_plural = "OTPs"

    def is_valid(self):
        """
        Vérifie si l'OTP est toujours valide en fonction de PASSWORD_RESET_TIMEOUT.
        Retourne True si valide, False sinon.
        """
        try:
            timeout_seconds = settings.PASSWORD_RESET_TIMEOUT * 60  # Convertit en secondes
        except AttributeError:
            raise ImproperlyConfigured(
                "Vous devez définir PASSWORD_RESET_TIMEOUT dans vos paramètres Django."
            )

        expiration_time = self.created_at + timezone.timedelta(seconds=timeout_seconds)
        return timezone.now() <= expiration_time