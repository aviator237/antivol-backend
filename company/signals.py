from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import PublicService
import requests
import logging

logger = logging.getLogger(__name__)

@receiver(pre_save, sender=PublicService)
def geocode_public_service_address(sender, instance, **kwargs):
    """
    Signal pour géocoder automatiquement l'adresse d'un service public
    et récupérer les coordonnées GPS, la ville et le code postal.
    
    Ce signal est déclenché avant la sauvegarde d'un PublicService.
    Si l'adresse est fournie mais que les coordonnées GPS sont manquantes,
    il utilise l'API de géocodage pour les récupérer.
    """
    # Vérifier si l'adresse est fournie mais que les coordonnées sont manquantes
    if instance.address and (instance.latitude is None or instance.longitude is None or 
                            not instance.city or not instance.postal_code):
        try:
            # Construire l'adresse complète pour la recherche
            search_address = instance.address
            if instance.city:
                search_address += f", {instance.city}"
            if instance.postal_code:
                search_address += f" {instance.postal_code}"
            
            # Appeler l'API de géocodage française
            response = requests.get(
                "https://api-adresse.data.gouv.fr/search/",
                params={"q": search_address, "limit": 1},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["features"] and len(data["features"]) > 0:
                    feature = data["features"][0]
                    properties = feature["properties"]
                    coordinates = feature["geometry"]["coordinates"]
                    
                    # Mettre à jour les coordonnées GPS
                    if instance.latitude is None or instance.longitude is None:
                        instance.longitude = coordinates[0]
                        instance.latitude = coordinates[1]
                    
                    # Mettre à jour la ville si elle n'est pas définie
                    if not instance.city and properties.get("city"):
                        instance.city = properties["city"]
                    
                    # Mettre à jour le code postal s'il n'est pas défini
                    if not instance.postal_code and properties.get("postcode"):
                        instance.postal_code = properties["postcode"]
                    
                    logger.info(f"Géocodage réussi pour {instance.name}: {instance.latitude}, {instance.longitude}")
                else:
                    logger.warning(f"Aucun résultat de géocodage trouvé pour l'adresse: {search_address}")
            else:
                logger.error(f"Erreur lors de l'appel à l'API de géocodage: {response.status_code}")
        
        except Exception as e:
            logger.error(f"Erreur lors du géocodage de l'adresse: {str(e)}")
