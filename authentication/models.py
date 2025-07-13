from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import random

def generate_verification_code():
    """Génère un code de vérification à 6 chiffres"""
    return str(random.randint(100000, 999999))

class EmailVerification(models.Model):
    """Modèle pour gérer la vérification des emails"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_verification')
    verification_token = models.UUIDField(default=uuid.uuid4, unique=True)
    verification_code = models.CharField(max_length=6, default=generate_verification_code)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Email verification for {self.user.email}"

    def verify(self):
        """Marque l'email comme vérifié"""
        self.is_verified = True
        self.verified_at = timezone.now()
        self.save()

    def regenerate_code(self):
        """Régénère un nouveau code de vérification"""
        self.verification_code = generate_verification_code()
        self.save()

    class Meta:
        verbose_name = "Vérification d'email"
        verbose_name_plural = "Vérifications d'emails"
