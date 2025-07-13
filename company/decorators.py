from functools import wraps
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.shortcuts import resolve_url, redirect
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test

from account.models import Profil, UserRole


def company_owner_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Décorateur pour les vues qui vérifie que l'utilisateur est connecté et est un administrateur d'entreprise.
    Si l'utilisateur est un administrateur d'entreprise mais n'a pas d'entreprise associée,
    il est redirigé vers la page de création d'entreprise.
    """
    def check_company_owner(user):
        """
        Vérifie si l'utilisateur est un administrateur d'entreprise.
        """
        if not user.is_authenticated:
            return False
        
        try:
            profile = Profil.objects.get(owner=user)
            return profile.role == UserRole.COMPANY_OWNER
        except Profil.DoesNotExist:
            return False

    actual_decorator = user_passes_test(
        check_company_owner,
        login_url=login_url,
        redirect_field_name=redirect_field_name,
    )
    
    if function:
        @wraps(function)
        def _wrapped_view(request, *args, **kwargs):
            # Vérifier si l'utilisateur a une entreprise associée
            try:
                profile = Profil.objects.get(owner=request.user)
                if profile.role == UserRole.COMPANY_OWNER and not profile.company:
                    messages.warning(request, "Vous devez d'abord créer une entreprise.")
                    return redirect('company:company_create')
            except Profil.DoesNotExist:
                pass
            
            return function(request, *args, **kwargs)
        
        return actual_decorator(_wrapped_view)
    
    return actual_decorator


def regular_user_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Décorateur pour les vues qui vérifie que l'utilisateur est connecté et est un utilisateur régulier.
    Si l'utilisateur est un administrateur d'entreprise, il est redirigé vers le tableau de bord de l'entreprise.
    """
    def check_regular_user(user):
        """
        Vérifie si l'utilisateur est un utilisateur régulier.
        """
        if not user.is_authenticated:
            return False
        
        try:
            profile = Profil.objects.get(owner=user)
            return profile.role == UserRole.REGULAR
        except Profil.DoesNotExist:
            # Si le profil n'existe pas, on considère que c'est un utilisateur régulier
            return True

    actual_decorator = user_passes_test(
        check_regular_user,
        login_url=login_url,
        redirect_field_name=redirect_field_name,
    )
    
    if function:
        @wraps(function)
        def _wrapped_view(request, *args, **kwargs):
            # Vérifier si l'utilisateur est un administrateur d'entreprise
            try:
                profile = Profil.objects.get(owner=request.user)
                if profile.role == UserRole.COMPANY_OWNER:
                    messages.info(request, "Vous êtes connecté en tant qu'administrateur d'entreprise.")
                    return redirect('company:dashboard')
            except Profil.DoesNotExist:
                pass
            
            return function(request, *args, **kwargs)
        
        return actual_decorator(_wrapped_view)
    
    return actual_decorator
