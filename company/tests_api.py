from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import Category, Company, Catalog
from django.contrib.auth.models import User
import tempfile
from django.core.files.uploadedfile import SimpleUploadedFile


class CompanyAPITests(TestCase):
    def setUp(self):
        # Créer un utilisateur pour les tests
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Créer des catégories
        self.category1 = Category.objects.create(name='Restauration', description='Restaurants et cafés')
        self.category2 = Category.objects.create(name='Informatique', description='Services informatiques')
        
        # Créer des entreprises
        self.company1 = Company.objects.create(
            name='Restaurant Test',
            category=self.category1,
            address='123 Rue Test',
            postal_code='75000',
            city='Paris',
            siret='12345678901234',
            latitude=48.8566,
            longitude=2.3522
        )
        
        self.company2 = Company.objects.create(
            name='Informatique Test',
            category=self.category2,
            address='456 Rue Test',
            postal_code='69000',
            city='Lyon',
            siret='98765432109876',
            latitude=45.7640,
            longitude=4.8357
        )
        
        # Créer un catalogue
        pdf_file = SimpleUploadedFile(
            "test.pdf",
            b"file_content",
            content_type="application/pdf"
        )
        
        self.catalog = Catalog.objects.create(
            title='Catalogue Test',
            file=pdf_file,
            company=self.company1,
            publisher=self.user
        )
        
        # Client API
        self.client = APIClient()
    
    def test_get_categories(self):
        """Test de récupération de la liste des catégories"""
        url = reverse('company:api_category_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['name'], 'Informatique')  # Ordre alphabétique
        self.assertEqual(response.data[1]['name'], 'Restauration')
    
    def test_get_companies_by_category(self):
        """Test de récupération des entreprises par catégorie"""
        url = reverse('company:api_company_list_by_category', args=[self.category1.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Restaurant Test')
    
    def test_get_company_detail(self):
        """Test de récupération des détails d'une entreprise"""
        url = reverse('company:api_company_detail', args=[self.company1.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Restaurant Test')
        self.assertEqual(response.data['category']['name'], 'Restauration')
    
    def test_get_catalogs_by_company(self):
        """Test de récupération des catalogues d'une entreprise"""
        url = reverse('company:api_catalog_list_by_company', args=[self.company1.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Catalogue Test')
    
    def test_get_catalog_detail(self):
        """Test de récupération des détails d'un catalogue"""
        url = reverse('company:api_catalog_detail', args=[self.catalog.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Catalogue Test')
        self.assertEqual(response.data['company']['name'], 'Restaurant Test')
    
    def test_search_companies_by_location(self):
        """Test de recherche d'entreprises par localisation"""
        url = reverse('company:api_company_search_by_location')
        response = self.client.get(url, {'lat': 48.8566, 'lng': 2.3522, 'radius': 10})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Restaurant Test')
        
        # Test avec un rayon plus grand
        response = self.client.get(url, {'lat': 48.8566, 'lng': 2.3522, 'radius': 500})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Les deux entreprises sont trouvées
    
    def tearDown(self):
        # Nettoyer les fichiers temporaires
        self.catalog.file.delete()
