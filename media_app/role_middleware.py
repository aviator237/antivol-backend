from django.shortcuts import redirect
from django.urls import resolve, Resolver404
from django.contrib import messages


class UserRoleMiddleware:

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
        