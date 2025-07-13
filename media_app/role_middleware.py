from django.shortcuts import redirect
from django.urls import resolve, Resolver404
from django.contrib import messages
from account.models import Profil, UserRole


class UserRoleMiddleware:
    """
    Middleware qui redirige les utilisateurs en fonction de leur rôle.
    - Les administrateurs d'entreprise sont redirigés vers la page d'accueil des entreprises
      s'ils tentent d'accéder aux URLs destinées aux utilisateurs classiques.
    - Les utilisateurs classiques sont redirigés vers leur page d'accueil
      s'ils tentent d'accéder aux URLs destinées aux administrateurs d'entreprise.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        
        # URLs réservées aux utilisateurs classiques
        self.regular_user_urls = [
            '/account/',
            '/album/',
        ]
        
        # URLs réservées aux administrateurs d'entreprise
        self.company_owner_urls = [
            '/company/',
        ]
        
        # URLs accessibles à tous les utilisateurs authentifiés
        self.common_urls = [
            '/auth/logout',
            '/pricing/',
            '/payments/',
        ]
        
        # URLs publiques (accessibles sans authentification)
        self.public_urls = [
            '/auth/login',
            '/auth/register',
            '/auth/activate',
            '/auth/reset_pwd',
            '/auth/new_password',
            '/auth/resent',
            '/company/public/catalogs/',
            '/company/api/',
            '/api-box/',
            '/admin/',
        ]

    def __call__(self, request):
        # Ignorer les requêtes pour les fichiers statiques et media
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return self.get_response(request)
        
        if request.user.is_superuser:
            return self.get_response(request)
        
        # Ignorer les URLs publiques
        for url in self.public_urls:
            if request.path.startswith(url):
                return self.get_response(request)
        
        # Vérifier si l'utilisateur est authentifié
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        # Ignorer les URLs communes
        for url in self.common_urls:
            if request.path.startswith(url):
                return self.get_response(request)
        
        # Vérifier le rôle de l'utilisateur
        try:
            profile = Profil.objects.get(owner=request.user)
            
            # Si l'utilisateur est un administrateur d'entreprise
            if profile.role == UserRole.COMPANY_OWNER:
                # Vérifier si l'utilisateur tente d'accéder à une URL réservée aux utilisateurs classiques
                for url in self.regular_user_urls:
                    if request.path.startswith(url):
                        messages.warning(request, "Redirection")
                        return redirect('/company/')
            
            # Si l'utilisateur est un utilisateur classique
            elif profile.role == UserRole.REGULAR:
                # Vérifier si l'utilisateur tente d'accéder à une URL réservée aux administrateurs d'entreprise
                for url in self.company_owner_urls:
                    if request.path.startswith(url):
                        messages.warning(request, "Cette page est réservée aux administrateurs d'entreprise. Vous avez été redirigé vers votre tableau de bord.")
                        return redirect('/account/')
        
        except Profil.DoesNotExist:
            # Si le profil n'existe pas, laisser passer la requête
            pass
        
        return self.get_response(request)
