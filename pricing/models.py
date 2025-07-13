from django.db import models
from django.contrib.auth.models import User
from enum import Enum
from django.core.exceptions import ValidationError
from django.utils.timezone import now


class StatusType(Enum):
    INACTIVE = "inactive", "Inactif"
    ACTIVE = "active", "Actif"
    CANCELED = "canceled", "Annulé"
    EXPIRED = "expired", "Expiré"

    @classmethod
    def choices(cls):
        return [(key.value[0], key.value[1]) for key in cls]

class PlanType(Enum):
    FREE = "free", "Gratuit"
    STANDARD = "standard", "Standard"
    CUSTOM = "custom", "Personnalisé"
    COMPANY_CATALOG = "company_catalog", "Catalogue Entreprise"

    @classmethod
    def choices(cls):
        return [(key.value[0], key.value[1]) for key in cls]

class Product(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='nom du produit')
    description = models.TextField(max_length=500, null=True, blank=True, unique=False, verbose_name='description du produit')
    storage = models.FloatField(verbose_name='stockage (Go)', blank=False, null=False)
    active = models.BooleanField(verbose_name='actif', default=True, blank=False, null=False)
    type = models.CharField(blank=False, null=False, max_length=20, default=PlanType.STANDARD.value[0], verbose_name="Type", choices=PlanType.choices())
    stripe_product_id = models.CharField(max_length=255, blank=True, null=True, verbose_name='stripe ID')
    created_at = models.DateTimeField(blank=True, null=True, auto_created=True, auto_now_add=True, verbose_name="date de création")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="dernière mise à jour")

    def __str__(self):
        return self.name

    def is_free(self):
        return self.type == PlanType.FREE.value[0]

    class Meta:
        ordering = ['-created_at']
        verbose_name = "produit"
        verbose_name_plural = "produits"

    def get_plans(self):
        return Plan.objects.filter(product=self)

    def clean(self):
        if self.type == PlanType.FREE.value:
            if Product.objects.filter(type=PlanType.FREE.value).exclude(id=self.id).exists():
                raise ValidationError("Vous ne pouvez pas créer plusieurs produits gratuits.")

class Plan(models.Model):
    class IntervalType(Enum):
        DAY = "day", "Jour"
        WEEK = "week", "Semaine"
        MONTH = "month", "Mois"
        YEAR = "year", "Année"

        @classmethod
        def choices(cls):
            return [(key.value[0], key.value[1]) for key in cls]

    product = models.ForeignKey(Product, null=False, on_delete=models.CASCADE, related_name='plans', verbose_name='produit')
    active = models.BooleanField(default=True, null=False, verbose_name='actif')
    amount = models.IntegerField(verbose_name='montant (€)', null=False)
    created_at = models.DateTimeField(blank=True, null=True, auto_created=True, auto_now_add=True, verbose_name="date de création")
    currency = models.CharField(max_length=4, default='EUR', verbose_name='devise')
    interval = models.CharField(max_length=10, verbose_name='intervalle', choices=IntervalType.choices(), default=IntervalType.MONTH.value[0])
    interval_count = models.IntegerField(verbose_name='nombre d\'intervalle', null=False, default=1)
    trial_period_days = models.IntegerField(null=True, default=0, blank=True, verbose_name='période d\'essai(jours)')
    stripe_plan_id = models.CharField(max_length=255, blank=True, null=True, verbose_name='stripe ID')

    def __str__(self):
        return f"{self.product.name} - {self.amount} {self.currency}/{self.interval}"

    def is_free(self):
        return self.product.is_free()

    class Meta:
        ordering = ['-created_at']
        verbose_name = "plan"
        verbose_name_plural = "plans"

    def get_interval_display(self):
        return dict(self.IntervalType.choices()).get(self.interval, self.interval)

class Subscription(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='users', verbose_name='utilisateur')
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='plans', verbose_name='plan')
    stripe_subscription_id = models.CharField(max_length=255, null=True, blank=True, verbose_name='ID de la souscription Stripe')
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True, verbose_name='ID de la session Stripe')
    status = models.CharField(max_length=10, editable=False, choices=StatusType.choices(), null=True, default=StatusType.INACTIVE.value[0], verbose_name='statut')
    current_period_start = models.DateTimeField(verbose_name='début de période', null=True, blank=True)
    current_period_end = models.DateTimeField(verbose_name='fin de période', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='date de création')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='dernière mise à jour')

    def __str__(self):
        return f"Subscription {self.id} - {self.user.username} - {self.plan.product.name}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "souscription"
        verbose_name_plural = "souscriptions"

    def check_and_update_status(self):
        """Check if the subscription is expired and update the status."""
        if self.current_period_end and self.current_period_end < now():
            self.status = StatusType.EXPIRED.value[0]
            self.save()
            self.disable_catalogs()

    def disable_catalogs(self):
        """Disable all catalogs associated with the user."""
        catalogs = self.user.catalog_set.all()
        catalogs.update(active=False)

    def enable_catalogs(self):
        """Enable all catalogs associated with the user."""
        catalogs = self.user.catalog_set.all()
        catalogs.update(active=True)

class Payment(models.Model):
    # user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments', verbose_name='utilisateur')
    subscription = models.ForeignKey(Subscription, null=True, on_delete=models.CASCADE, related_name='payments', verbose_name='Souscription')
    stripe_payment_intent_id = models.CharField(max_length=255, verbose_name='ID de l\'intent de paiement Stripe')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='montant (€)')
    currency = models.CharField(max_length=10, verbose_name='devise')
    status = models.CharField(max_length=50, verbose_name='statut')
    billing_reason = models.CharField(max_length=255, null=True, blank=True, verbose_name='raison de facturation')
    created = models.DateTimeField(null=True, blank=True, verbose_name='date de création stripe')
    customer_email = models.EmailField(null=True, blank=True, verbose_name='email du client')
    hosted_invoice_url = models.URLField(null=True, blank=True, verbose_name='URL de la facture hébergée')
    invoice_pdf = models.URLField(null=True, blank=True, verbose_name='PDF de la facture')
    stripe_invoice_id = models.CharField(max_length=255, null=True, blank=True, verbose_name='ID de la facture Stripe')
    paid = models.BooleanField(default=False, verbose_name='payé')
    period_end = models.DateTimeField(null=True, blank=True, verbose_name='fin de période')
    period_start = models.DateTimeField(null=True, blank=True, verbose_name='début de période')
    amount_due = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='montant dû')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='montant payé')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='date de création')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='date de mise à jour')

    def __str__(self):
        return f"Payment {self.id} - {self.user.username} - {self.amount} {self.currency}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "paiement"
        verbose_name_plural = "paiements"















