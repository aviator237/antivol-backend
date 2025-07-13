from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from account.models import Profil, UserRole
from company.models import Company, Category


class RoleMiddlewareTest(TestCase):
    def setUp(self):
        # Créer un utilisateur classique
        self.regular_user = User.objects.create_user(
            username='regular_user',
            email='regular@example.com',
            password='password123',
            is_active=True
        )
        self.regular_profile = Profil.objects.create(
            owner=self.regular_user,
            role=UserRole.REGULAR
        )
        
        # Créer un utilisateur administrateur d'entreprise
        self.company_user = User.objects.create_user(
            username='company_user',
            email='company@example.com',
            password='password123',
            is_active=True
        )
        
        # Créer une catégorie et une entreprise
        self.category = Category.objects.create(
            name='Test Category',
            description='Test Description'
        )
        
        self.company = Company.objects.create(
            name='Test Company',
            category=self.category,
            address='123 Test Street',
            postal_code='12345',
            city='Test City',
            siret='12345678901234'
        )
        
        self.company_profile = Profil.objects.create(
            owner=self.company_user,
            role=UserRole.COMPANY_OWNER,
            company=self.company
        )
        
        # Créer des clients pour les tests
        self.regular_client = Client()
        self.company_client = Client()
        
        # Connecter les clients
        self.regular_client.login(username='regular_user', password='password123')
        self.company_client.login(username='company_user', password='password123')
    
    def test_regular_user_accessing_company_urls(self):
        """Tester qu'un utilisateur classique est redirigé s'il tente d'accéder à une URL d'entreprise"""
        response = self.regular_client.get('/company/', follow=True)
        
        # Vérifier que l'utilisateur est redirigé vers la page d'accueil des utilisateurs classiques
        self.assertRedirects(response, '/account/')
        
        # Vérifier qu'un message d'avertissement est affiché
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Cette page est réservée aux administrateurs d'entreprise. Vous avez été redirigé vers votre tableau de bord.")
    
    def test_company_user_accessing_regular_urls(self):
        """Tester qu'un administrateur d'entreprise est redirigé s'il tente d'accéder à une URL d'utilisateur classique"""
        response = self.company_client.get('/account/', follow=True)
        
        # Vérifier que l'utilisateur est redirigé vers la page d'accueil des entreprises
        self.assertRedirects(response, '/company/')
        
        # Vérifier qu'un message d'avertissement est affiché
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Cette page est réservée aux utilisateurs classiques. Vous avez été redirigé vers votre tableau de bord d'entreprise.")
    
    def test_regular_user_accessing_regular_urls(self):
        """Tester qu'un utilisateur classique peut accéder à ses propres URLs"""
        response = self.regular_client.get('/account/')
        
        # Vérifier que l'utilisateur n'est pas redirigé
        self.assertEqual(response.status_code, 200)
    
    def test_company_user_accessing_company_urls(self):
        """Tester qu'un administrateur d'entreprise peut accéder à ses propres URLs"""
        response = self.company_client.get('/company/')
        
        # Vérifier que l'utilisateur n'est pas redirigé
        self.assertEqual(response.status_code, 200)
    
    def test_both_users_accessing_common_urls(self):
        """Tester que les deux types d'utilisateurs peuvent accéder aux URLs communes"""
        # Tester l'accès à la page de tarification pour l'utilisateur classique
        response_regular = self.regular_client.get('/pricing/')
        self.assertEqual(response_regular.status_code, 200)
        
        # Tester l'accès à la page de tarification pour l'administrateur d'entreprise
        response_company = self.company_client.get('/pricing/')
        self.assertEqual(response_company.status_code, 200)
