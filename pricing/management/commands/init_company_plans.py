from django.core.management.base import BaseCommand
from pricing.models import Product, Plan, PlanType

class Command(BaseCommand):
    help = 'Initialize company catalog subscription plans'

    def handle(self, *args, **options):
        # Créer le produit pour les catalogues d'entreprise
        company_catalog_product, created = Product.objects.get_or_create(
            name="Abonnement Catalogue Entreprise",
            defaults={
                'description': "Publiez vos catalogues de publicité sur la plateforme",
                'type': PlanType.COMPANY_CATALOG.value[0],
                'storage': 0,  # Pas de stockage associé
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created product: {company_catalog_product.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Product already exists: {company_catalog_product.name}'))
        
        # Créer les plans pour les catalogues d'entreprise
        plans_data = [
            {
                'name': 'ABCAT1M',
                'amount': 29,
                'interval': 'month',
                'interval_count': 1,
                'description': 'Abonnement mensuel pour la publication de catalogues'
            },
            {
                'name': 'ABCAT3M',
                'amount': 79,
                'interval': 'month',
                'interval_count': 3,
                'description': 'Abonnement trimestriel pour la publication de catalogues'
            },
            {
                'name': 'ABCAT12M',
                'amount': 290,
                'interval': 'year',
                'interval_count': 1,
                'description': 'Abonnement annuel pour la publication de catalogues (1 mois gratuit)'
            }
        ]
        
        for plan_data in plans_data:
            plan, created = Plan.objects.get_or_create(
                product=company_catalog_product,
                interval=plan_data['interval'],
                interval_count=plan_data['interval_count'],
                defaults={
                    'amount': plan_data['amount'],
                    'currency': 'EUR',
                    'active': True,
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created plan: {plan_data["name"]} - {plan}'))
            else:
                self.stdout.write(self.style.WARNING(f'Plan already exists: {plan_data["name"]} - {plan}'))
                
        self.stdout.write(self.style.SUCCESS('Company catalog subscription plans initialized successfully'))
