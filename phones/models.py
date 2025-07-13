from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class Phone(models.Model):
    """Modèle représentant un appareil mobile de l'utilisateur"""
    
    # Choix pour le système d'exploitation
    OS_CHOICES = [
        ('android', 'Android'),
        ('ios', 'iOS'),
        ('other', 'Autre'),
    ]
    
    # Choix pour le statut de l'appareil
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('inactive', 'Inactif'),
        ('lost', 'Perdu'),
        ('stolen', 'Volé'),
        ('blocked', 'Bloqué'),
    ]
    
    # Informations de base
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='phones')
    device_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=100, help_text="Nom donné à l'appareil par l'utilisateur")
    
    # Informations techniques
    brand = models.CharField(max_length=50, blank=True, help_text="Marque de l'appareil (Samsung, Apple, etc.)")
    model = models.CharField(max_length=100, blank=True, help_text="Modèle de l'appareil")
    os_type = models.CharField(max_length=10, choices=OS_CHOICES, default='android')
    os_version = models.CharField(max_length=20, blank=True, help_text="Version du système d'exploitation")
    app_version = models.CharField(max_length=20, blank=True, help_text="Version de l'app Antivol")
    
    # Identifiants uniques
    imei = models.CharField(max_length=20, blank=True, help_text="IMEI de l'appareil")
    serial_number = models.CharField(max_length=50, blank=True, help_text="Numéro de série")
    
    # Statut et sécurité
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    is_primary = models.BooleanField(default=False, help_text="Appareil principal de l'utilisateur")
    last_seen = models.DateTimeField(auto_now=True, help_text="Dernière activité de l'appareil")
    
    # Paramètres de sécurité
    unlock_attempts_threshold = models.PositiveIntegerField(
        default=3, 
        help_text="Nombre de tentatives échouées avant déclenchement"
    )
    photo_capture_enabled = models.BooleanField(
        default=True, 
        help_text="Capture de photos lors de tentatives échouées"
    )
    location_tracking_enabled = models.BooleanField(
        default=True, 
        help_text="Suivi de localisation activé"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Téléphone"
        verbose_name_plural = "Téléphones"
        ordering = ['-is_primary', '-last_seen']
        unique_together = ['user', 'device_id']
    
    def __str__(self):
        return f"{self.name} ({self.user.get_full_name() or self.user.username})"
    
    def save(self, *args, **kwargs):
        # S'assurer qu'un seul appareil est marqué comme principal par utilisateur
        if self.is_primary:
            Phone.objects.filter(user=self.user, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)
    
    @property
    def is_online(self):
        """Vérifie si l'appareil est considéré comme en ligne (activité récente)"""
        if not self.last_seen:
            return False
        return (timezone.now() - self.last_seen).total_seconds() < 300  # 5 minutes
    
    @property
    def display_name(self):
        """Nom d'affichage de l'appareil"""
        if self.brand and self.model:
            return f"{self.name} ({self.brand} {self.model})"
        return self.name


class UnlockAttempt(models.Model):
    """Modèle pour enregistrer les tentatives de déverrouillage"""
    
    ATTEMPT_TYPES = [
        ('pin', 'Code PIN'),
        ('pattern', 'Schéma'),
        ('password', 'Mot de passe'),
        ('fingerprint', 'Empreinte digitale'),
        ('face', 'Reconnaissance faciale'),
        ('other', 'Autre'),
    ]
    
    RESULT_CHOICES = [
        ('success', 'Réussi'),
        ('failed', 'Échoué'),
        ('blocked', 'Bloqué'),
    ]
    
    phone = models.ForeignKey(Phone, on_delete=models.CASCADE, related_name='unlock_attempts')
    attempt_type = models.CharField(max_length=20, choices=ATTEMPT_TYPES, default='pin')
    result = models.CharField(max_length=10, choices=RESULT_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Informations de localisation (optionnel)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    location_accuracy = models.FloatField(null=True, blank=True, help_text="Précision en mètres")
    
    # Métadonnées
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Tentative de déverrouillage"
        verbose_name_plural = "Tentatives de déverrouillage"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.phone.name} - {self.get_result_display()} ({self.timestamp.strftime('%d/%m/%Y %H:%M')})"
    
    @property
    def is_suspicious(self):
        """Détermine si cette tentative est suspecte"""
        if self.result == 'failed':
            # Compter les tentatives échouées récentes
            recent_failures = UnlockAttempt.objects.filter(
                phone=self.phone,
                result='failed',
                timestamp__gte=timezone.now() - timezone.timedelta(minutes=10)
            ).count()
            return recent_failures >= self.phone.unlock_attempts_threshold
        return False


class IntrusionPhoto(models.Model):
    """Modèle pour stocker les photos prises lors de tentatives d'intrusion"""
    
    unlock_attempt = models.ForeignKey(
        UnlockAttempt, 
        on_delete=models.CASCADE, 
        related_name='photos'
    )
    photo = models.ImageField(
        upload_to='intrusion_photos/%Y/%m/%d/',
        help_text="Photo prise lors de la tentative d'intrusion"
    )
    camera_type = models.CharField(
        max_length=10,
        choices=[('front', 'Frontale'), ('back', 'Arrière')],
        default='front'
    )
    file_size = models.PositiveIntegerField(help_text="Taille du fichier en octets")
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Métadonnées EXIF (optionnel)
    exif_data = models.JSONField(blank=True, null=True, help_text="Données EXIF de la photo")
    
    class Meta:
        verbose_name = "Photo d'intrusion"
        verbose_name_plural = "Photos d'intrusion"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Photo {self.camera_type} - {self.unlock_attempt.phone.name} ({self.timestamp.strftime('%d/%m/%Y %H:%M')})"
    
    def save(self, *args, **kwargs):
        if self.photo:
            self.file_size = self.photo.size
        super().save(*args, **kwargs)
