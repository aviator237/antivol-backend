from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
import os
from django_clamd.validators import validate_file_infection
from django.core.validators import FileExtensionValidator



class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="nom")
    description = models.TextField(blank=True, null=True, verbose_name="description")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['name']


class Company(models.Model):
    name = models.CharField(max_length=255, verbose_name="nom")
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='companies',
        verbose_name="Catégorie"
    )
    address = models.CharField(max_length=255, verbose_name="adresse")
    postal_code = models.CharField(max_length=10, verbose_name="code postal")
    city = models.CharField(max_length=100, verbose_name="ville")
    siret = models.CharField(max_length=14, verbose_name="SIRET")

    # Geographical coordinates
    latitude = models.FloatField(verbose_name="Latitude", null=True, blank=True)
    longitude = models.FloatField(verbose_name="Longitude", null=True, blank=True)

    # Heures d'ouverture et de fermeture
    opening_hour = models.TimeField(verbose_name="Heure d'ouverture", default="08:00", null=True, blank=True)
    closing_hour = models.TimeField(verbose_name="Heure de fermeture", default="16:00", null=True, blank=True)

    # Date de création de l'entreprise
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    # Statut de l'entreprise
    is_active = models.BooleanField(default=True, verbose_name="Entreprise active")
    is_banned = models.BooleanField(default=False, verbose_name="Entreprise bannie")

    def __str__(self):
        return self.name

    def is_in_trial_period(self):
        """
        Vérifie si l'entreprise est dans sa période d'essai gratuite (1 mois).
        Retourne True si l'entreprise est dans sa période d'essai, False sinon.
        """
        from datetime import timedelta
        from django.utils import timezone

        # Période d'essai de 1 mois (30 jours)
        trial_period = timedelta(days=30)

        # Vérifier si la période d'essai est toujours active
        return timezone.now() <= (self.created_at + trial_period)

    def has_active_subscription(self):
        """
        Vérifie si l'entreprise a un abonnement actif.
        Retourne True si l'entreprise a un abonnement actif, False sinon.
        """
        from pricing.models import Subscription, StatusType
        from account.models import Profil

        # Récupérer les profils associés à cette entreprise
        profiles = Profil.objects.filter(company=self)

        # Vérifier si au moins un profil a un abonnement actif
        for profile in profiles:
            if profile.owner:
                subscriptions = Subscription.objects.filter(
                    user=profile.owner,
                    status=StatusType.ACTIVE.value[0],
                    plan__product__type='company_catalog'
                )
                if subscriptions.exists():
                    return True

        return False

    def can_manage_catalogs(self):
        """
        Vérifie si l'entreprise peut gérer (créer, modifier, supprimer) ses catalogues.
        Une entreprise peut gérer ses catalogues si elle est dans sa période d'essai
        ou si elle a un abonnement actif.
        """
        return self.is_in_trial_period() or self.has_active_subscription()

    def are_catalogs_visible(self):
        """
        Vérifie si les catalogues de l'entreprise sont visibles pour les clients.
        Les catalogues sont visibles si l'entreprise est dans sa période d'essai
        ou si elle a un abonnement actif.
        """
        return self.is_in_trial_period() or self.has_active_subscription()

    def reactivate(self):
        """
        Réactive une entreprise désactivée.
        Cette méthode est utilisée lorsqu'une entreprise souscrit à un abonnement
        après avoir été désactivée suite à l'expiration de sa période d'essai.
        """
        if not self.is_active and not self.is_banned:
            self.is_active = True
            self.save()
            return True
        return False

    def get_trial_status(self):
        """
        Retourne des informations détaillées sur le statut d'essai de l'entreprise.

        Returns:
            dict: Un dictionnaire contenant les informations suivantes:
                - is_trial (bool): True si l'entreprise est en période d'essai, False sinon
                - days_remaining (int): Nombre de jours restants dans la période d'essai (0 si hors période)
                - end_date (datetime): Date de fin de la période d'essai
                - has_subscription (bool): True si l'entreprise a un abonnement actif, False sinon
                - catalogs_count (int): Nombre de catalogues publiés par l'entreprise
                - max_catalogs (int): Nombre maximum de catalogues autorisés en période d'essai (1)
                - can_create_catalog (bool): True si l'entreprise peut créer un nouveau catalogue
                - is_active (bool): True si l'entreprise est active, False sinon
                - is_banned (bool): True si l'entreprise est bannie, False sinon
                - trial_expired (bool): True si la période d'essai est expirée et pas d'abonnement, False sinon
        """
        from datetime import timedelta
        from django.utils import timezone

        # Période d'essai de 1 mois (30 jours)
        trial_period = timedelta(days=30)
        trial_end_date = self.created_at + trial_period
        is_trial = timezone.now() <= trial_end_date

        # Calculer le nombre de jours restants dans la période d'essai
        if is_trial:
            days_remaining = (trial_end_date - timezone.now()).days
        else:
            days_remaining = 0

        # Vérifier si l'entreprise a un abonnement actif
        has_subscription = self.has_active_subscription()

        # Compter le nombre de catalogues publiés par l'entreprise
        catalogs_count = self.catalogs.count()

        # Nombre maximum de catalogues autorisés en période d'essai
        max_catalogs = 1

        # Déterminer si l'entreprise peut créer un nouveau catalogue
        can_create_catalog = has_subscription or (is_trial and catalogs_count < max_catalogs)

        # Déterminer si la période d'essai est expirée et qu'il n'y a pas d'abonnement
        trial_expired = not is_trial and not has_subscription

        # Si la période d'essai est expirée et qu'il n'y a pas d'abonnement,
        # l'entreprise ne devrait pas être active sauf si elle est explicitement activée
        if trial_expired and not self.is_active:
            can_create_catalog = False

        return {
            'is_trial': is_trial,
            'days_remaining': days_remaining,
            'end_date': trial_end_date,
            'has_subscription': has_subscription,
            'catalogs_count': catalogs_count,
            'max_catalogs': max_catalogs,
            'can_create_catalog': can_create_catalog,
            'is_active': self.is_active,
            'is_banned': self.is_banned,
            'trial_expired': trial_expired
        }

    class Meta:
        verbose_name = "Entreprise"
        verbose_name_plural = "Entreprises"


class DistributionZone(models.Model):
    """Modèle pour les zones de diffusion des catalogues"""
    name = models.CharField(max_length=100, verbose_name="Nom de la ville")
    latitude = models.FloatField(verbose_name="Latitude")
    longitude = models.FloatField(verbose_name="Longitude")
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='distribution_zones',
        verbose_name="Entreprise"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")

    def __str__(self):
        return f"{self.name} - {self.company.name}"

    class Meta:
        verbose_name = "Zone de diffusion"
        verbose_name_plural = "Zones de diffusion"
        ordering = ['name']
        # Assurer l'unicité des zones pour une entreprise
        unique_together = ['name', 'company']


def catalog_file_path(instance, filename):
    """Générer un chemin de fichier pour les catalogues"""
    # Obtenir l'extension du fichier
    ext = filename.split('.')[-1]
    # Créer un nouveau nom de fichier avec l'ID de l'entreprise et le titre du catalogue
    filename = f"{instance.company.id}_{instance.title.replace(' ', '_')}.{ext}"
    # Retourner le chemin complet
    return os.path.join('catalogs', filename)


class Catalog(models.Model):
    """Modèle pour les catalogues d'entreprises"""
    title = models.CharField(max_length=255, verbose_name="Titre")
    file = models.FileField(upload_to=catalog_file_path, verbose_name="Fichier PDF", validators=[validate_file_infection, FileExtensionValidator(['pdf'])])
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='catalogs',
        verbose_name="Entreprise"
    )
    publisher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='published_catalogs',
        verbose_name="Publié par"
    )
    distribution_zones = models.ManyToManyField(
        DistributionZone,
        related_name='catalogs',
        verbose_name="Zones de diffusion"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")

    def __str__(self):
        return f"{self.title} - {self.company.name}"

    def filename(self):
        """Retourne le nom du fichier sans le chemin"""
        return os.path.basename(self.file.name)

    class Meta:
        verbose_name = "Catalogue"
        verbose_name_plural = "Catalogues"
        ordering = ['-created_at']


class PublicService(models.Model):
    """Modèle pour les services publics (mairies et pharmacies de garde)"""

    class ServiceType(models.TextChoices):
        CITY_HALL = 'city_hall', _('Mairie')
        PHARMACY = 'pharmacy', _('Pharmacie de garde')

    name = models.CharField(max_length=255, verbose_name="Nom")
    service_type = models.CharField(
        max_length=20,
        choices=ServiceType.choices,
        verbose_name="Type de service", default=ServiceType.CITY_HALL
    )
    address = models.CharField(max_length=255, verbose_name="Adresse")
    postal_code = models.CharField(max_length=10, verbose_name="Code postal", blank=True)
    city = models.CharField(max_length=100, verbose_name="Ville", blank=True, null=True)
    phone = models.CharField(max_length=40, verbose_name="Téléphone", blank=True, null=True)
    email = models.EmailField(verbose_name="Email", blank=True, null=True)
    website = models.URLField(verbose_name="Site web", blank=True, null=True)

    # Coordonnées géographiques
    latitude = models.FloatField(verbose_name="Latitude", null=True, blank=True)
    longitude = models.FloatField(verbose_name="Longitude", null=True, blank=True)

    # Horaires d'ouverture et de fermeture (par défaut: 19h00-09h00)
    opening_hour = models.TimeField(verbose_name="Heure d'ouverture", default='19:00:00', db_default='19:00:00')
    closing_hour = models.TimeField(verbose_name="Heure de fermeture", default='09:00:00', db_default='09:00:00')

    # Champ pour les notes ou informations supplémentaires
    notes = models.TextField(verbose_name="Notes", blank=True, null=True)

    # Dates de création et de mise à jour
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")

    def __str__(self):
        return f"{self.get_service_type_display()} - {self.name} ({self.city or 'Ville non spécifiée'})"

    def get_full_address(self):
        """Retourne l'adresse complète formatée"""
        parts = []
        if self.address:
            parts.append(self.address)
        if self.postal_code:
            parts.append(self.postal_code)
        if self.city:
            parts.append(self.city)
        return " ".join(parts) if parts else ""

    def get_google_maps_url(self):
        """Retourne l'URL Google Maps pour ce service"""
        if self.latitude and self.longitude:
            return f"https://www.google.com/maps?q={self.latitude},{self.longitude}"
        elif self.address:
            # Si pas de coordonnées mais une adresse, utiliser l'adresse
            full_address = self.get_full_address()
            if full_address:
                address = full_address.replace(" ", "+")
                return f"https://www.google.com/maps?q={address}"
        return None

    class Meta:
        verbose_name = "Service public"
        verbose_name_plural = "Services publics"
        ordering = ['service_type', 'city', 'name']
        # Assurer l'unicité du service dans une ville
        unique_together = ['service_type', 'name', 'city']
