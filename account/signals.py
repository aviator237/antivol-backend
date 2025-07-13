from datetime import timedelta
from django.utils.timezone import now
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profil
from pricing.models import Subscription, Plan, StatusType

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        try:
            Profil.objects.create(owner=instance)
            # Créer un abonnement d'essai pour l'utilisateur
            trial_plan = Plan.objects.filter(product__type='free', active=True).first()
            if trial_plan:
                Subscription.objects.create(
                    user=instance,
                    plan=trial_plan,
                    status=StatusType.ACTIVE.value[0],
                    current_period_start=now(),
                    current_period_end=now() + timedelta(days=30)
                )
        except Exception as e:
            pass  # Gérer les erreurs si nécessaire