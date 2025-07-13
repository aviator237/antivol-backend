from django.contrib.auth.models import User
from django.db import models
from pricing.models import Plan
from company.models import Company

class UserRole(models.TextChoices):
    REGULAR = 'regular', 'Utilisateur régulier'
    COMPANY_OWNER = 'company_owner', 'Propriétaire d\'entreprise'

class Profil(models.Model):
    owner = models.OneToOneField(User, blank=False, null=True, verbose_name='propriétaire', on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, blank=True, null=True, verbose_name='plan associé', on_delete=models.SET_NULL)
    created_at = models.DateTimeField(blank=True, null=True, auto_created=True, auto_now_add=True, verbose_name="date de création")
    stripe_customer_id = models.CharField(max_length=255, null=True, verbose_name='stripe ID')
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.REGULAR,
        verbose_name="Rôle de l'utilisateur"
    )


    last_updated = models.DateTimeField(auto_now=True, verbose_name="dernière mise à jour")
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profiles',
        verbose_name="Entreprise associée"
    )

    def is_company_owner(self):
            return self.role == UserRole.COMPANY_OWNER

    def __str__(self):
        return str(self.owner)

    class Meta:
        verbose_name = "profil"
        verbose_name_plural = "profils"


        