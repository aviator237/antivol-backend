"""
Tâches cron pour l'application company.
Ce fichier contient les fonctions qui seront exécutées par django-crontab.
"""
import logging
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import Company
from account.models import Profil

# Configurer le logger
logger = logging.getLogger(__name__)

def check_trial_status():
    """
    Vérifie le statut des périodes d'essai des entreprises et désactive celles
    dont la période d'essai a expiré et qui n'ont pas souscrit à un abonnement.
    """
    now = timezone.now()
    trial_period = timedelta(days=30)
    
    # Trouver les entreprises dont la période d'essai a expiré et qui n'ont pas d'abonnement
    expired_companies = []
    for company in Company.objects.filter(is_active=True, is_banned=False):
        trial_status = company.get_trial_status()
        if trial_status['trial_expired'] and not trial_status['has_subscription']:
            expired_companies.append(company)
    
    # Désactiver ces entreprises
    for company in expired_companies:
        company.is_active = False
        company.save()
        logger.warning(f'Entreprise désactivée: {company.name} (ID: {company.id})')
        
        # Envoyer un email de notification à tous les administrateurs de l'entreprise
        send_expiration_email(company)
    
    if expired_companies:
        logger.info(f'{len(expired_companies)} entreprise(s) désactivée(s) suite à l\'expiration de leur période d\'essai')
    else:
        logger.info('Aucune entreprise n\'a sa période d\'essai expirée')
    
    return f'{len(expired_companies)} entreprise(s) désactivée(s)'

def send_trial_expiration_reminders():
    """
    Envoie des notifications aux entreprises dont la période d'essai va bientôt expirer.
    Par défaut, les notifications sont envoyées 7 jours avant l'expiration.
    """
    now = timezone.now()
    trial_period = timedelta(days=30)
    notification_threshold = timedelta(days=7)  # Envoyer une notification 7 jours avant l'expiration
    
    # Trouver les entreprises dont la période d'essai va bientôt expirer
    companies_to_notify = []
    for company in Company.objects.filter(is_active=True, is_banned=False):
        trial_end_date = company.created_at + trial_period
        days_remaining = (trial_end_date - now).days
        
        # Si la période d'essai expire dans exactement 7 jours et l'entreprise n'a pas d'abonnement
        if days_remaining == notification_threshold.days and not company.has_active_subscription():
            companies_to_notify.append((company, days_remaining))
    
    # Envoyer des notifications à ces entreprises
    for company, days_remaining in companies_to_notify:
        send_reminder_email(company, days_remaining)
        logger.warning(f'Notification envoyée à {company.name} (ID: {company.id}) - {days_remaining} jour(s) restant(s)')
    
    if companies_to_notify:
        logger.info(f'{len(companies_to_notify)} entreprise(s) notifiée(s) de l\'expiration prochaine de leur période d\'essai')
    else:
        logger.info('Aucune entreprise n\'a sa période d\'essai qui expire prochainement')
    
    return f'{len(companies_to_notify)} entreprise(s) notifiée(s)'

def send_expiration_email(company):
    """Envoie un email de notification d'expiration de la période d'essai"""
    # Récupérer tous les administrateurs de l'entreprise
    admin_profiles = Profil.objects.filter(company=company, role='company_owner')
    
    for profile in admin_profiles:
        if profile.owner and profile.owner.email:
            subject = "Votre période d'essai a expiré"
            message = f"""
            Bonjour {profile.owner.first_name},
            
            Votre période d'essai pour l'entreprise {company.name} a expiré.
            
            Votre compte a été désactivé. Pour continuer à utiliser nos services, veuillez souscrire à un abonnement en vous connectant à votre compte.
            
            Cordialement,
            L'équipe Media
            """
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [profile.owner.email],
                    fail_silently=False,
                )
                logger.info(f"Email d'expiration envoyé à {profile.owner.email}")
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de l'email à {profile.owner.email}: {str(e)}")

def send_reminder_email(company, days_remaining):
    """Envoie un email de rappel avant l'expiration de la période d'essai"""
    # Récupérer tous les administrateurs de l'entreprise
    admin_profiles = Profil.objects.filter(company=company, role='company_owner')
    
    for profile in admin_profiles:
        if profile.owner and profile.owner.email:
            subject = f"Votre période d'essai expire dans {days_remaining} jour(s)"
            message = f"""
            Bonjour {profile.owner.first_name},
            
            Votre période d'essai pour l'entreprise {company.name} expire dans {days_remaining} jour(s).
            
            Pour continuer à utiliser nos services après cette date, veuillez souscrire à un abonnement en vous connectant à votre compte.
            
            Cordialement,
            L'équipe Media
            """
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [profile.owner.email],
                    fail_silently=False,
                )
                logger.info(f"Email de rappel envoyé à {profile.owner.email}")
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de l'email à {profile.owner.email}: {str(e)}")
