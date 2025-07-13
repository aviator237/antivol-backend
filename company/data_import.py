import json
import os
import logging
import threading
import time
import random
import requests
import re
import unicodedata
from django.conf import settings
from .models import PublicService

logger = logging.getLogger(__name__)

# Configuration pour le rate limiting
RATE_LIMIT_DELAY = 1.0  # Délai de base entre les requêtes en secondes
MAX_RETRIES = 3  # Nombre maximum de tentatives en cas d'erreur de rate limit
BACKOFF_FACTOR = 2  # Facteur de multiplication pour le backoff exponentiel
JITTER = 0.5  # Facteur de variation aléatoire pour éviter les requêtes synchronisées

def fix_encoding(text):
    """
    Corrige les problèmes d'encodage courants dans les textes
    """
    if not text:
        return text

    # Dictionnaire de substitutions pour les caractères mal encodés courants
    substitutions = {
        '√©': 'é',
        '√®': 'è',
        '√®': 'è',
        '√†': 'à',
        '√™': 'ê',
        '√´': 'ë',
        '√Æ': 'î',
        '√¨': 'ì',
        '√≤': 'ò',
        '√≥': 'ó',
        '√π': 'ù',
        '√∫': 'ú',
        '√º': 'ü',
        '√ß': 'ç',
        '√á': 'Ç',
        '√â': 'Â',
        '√Ä': 'Ä',
        '√Ö': 'Å',
        '√Ü': 'Ü',
        '√£': 'ã',
        '√±': 'ñ',
        '√ì': 'Ñ',
        '‚Äô': "'",
        '‚Äù': '"',
        '‚Äú': '"',
        '‚Äî': '—',
        '‚Äì': '–',
        '‚Ä¢': '•',
        '‚Ä°': '€',
        '‚Ä¶': '…',
        '‚Ä§': '§',
        '‚Ä©': '©',
        '‚Ä®': '®',
        '‚Ä´': '´',
        '‚Ä¨': '¨',
    }

    # Appliquer les substitutions
    for bad, good in substitutions.items():
        text = text.replace(bad, good)

    # Essayer de normaliser les caractères Unicode
    try:
        # Normaliser les caractères composés (comme é) en leurs composants (e + ´)
        text = unicodedata.normalize('NFKD', text)
        # Recombiner les caractères décomposés
        text = unicodedata.normalize('NFKC', text)
    except Exception as e:
        logger.warning(f"Erreur lors de la normalisation Unicode: {e}")

    # Supprimer les caractères de contrôle et autres caractères non imprimables
    text = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)

    return text

def load_json_file(file_path):
    """
    Load data from a JSON file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        logger.error(f"Error loading JSON file {file_path}: {str(e)}")
        return None

def import_mairies_data(file_path):
    """
    Import data from mairies.json file
    """
    data = load_json_file(file_path)
    if not data:
        return {"success": False, "message": "Failed to load data file", "imported": 0, "errors": 0}

    imported = 0
    errors = 0

    for item in data:
        try:
            # Extract data from JSON and fix encoding issues
            raw_name = item.get('NomOrganisme', '')
            name = fix_encoding(raw_name)
            print(f"Original: {raw_name} -> Fixed: {name}")

            if not name:
                logger.warning(f"Skipping record with no name: {item}")
                errors += 1
                continue

            # Extract city name from the mairie name
            city_name = name.replace('Mairie de ', '').replace('Mairie d\'', '').replace('Mairie du ', '')

            # Handle latitude and longitude - convert empty strings to None
            latitude = item.get('Latitude')
            if latitude == '':
                latitude = None

            longitude = item.get('Longitude')
            if longitude == '':
                longitude = None

            # Si les coordonnées sont manquantes, essayer de les obtenir par géocodage
            if (latitude is None or longitude is None) and item.get('Adresse'):
                # Attendre un peu pour respecter le rate limiting
                wait_for_rate_limit()

                # Essayer de géocoder l'adresse (avec correction d'encodage)
                address = fix_encoding(item.get('Adresse', ''))
                postal_code = str(item.get('CodePostal', ''))
                city_name = name.replace('Mairie de ', '').replace('Mairie d\'', '').replace('Mairie du ', '')

                logger.info(f"Tentative de géocodage pour {name}: {address}, {postal_code}, {city_name}")
                geo_lat, geo_lon = geocode_address(address, postal_code, city_name)

                if geo_lat and geo_lon:
                    latitude = geo_lat
                    longitude = geo_lon
                    logger.info(f"Géocodage réussi pour {name}: {latitude}, {longitude}")
                else:
                    logger.warning(f"Échec du géocodage pour {name}")

                # Attendre entre les requêtes pour respecter le rate limiting
                wait_for_rate_limit()

            # Check if a record with this name already exists
            existing_services = PublicService.objects.filter(
                name=name,
                service_type=PublicService.ServiceType.CITY_HALL
            )

            if existing_services.count() > 1:
                # If multiple records exist, delete all but keep the first one
                first_service = existing_services.first()
                existing_services.exclude(id=first_service.id).delete()

                # Update the remaining record (avec correction d'encodage)
                first_service.address = fix_encoding(item.get('Adresse', ''))
                first_service.postal_code = str(item.get('CodePostal', ''))
                first_service.city = fix_encoding(city_name)
                first_service.phone = fix_encoding(item.get('Téléphone', ''))
                first_service.email = fix_encoding(item.get('Email', ''))
                first_service.website = fix_encoding(item.get('Url', ''))
                first_service.latitude = latitude
                first_service.longitude = longitude
                first_service.notes = f"Code INSEE: {item.get('codeInsee', '')}, Mise à jour: {fix_encoding(item.get('dateMiseAJour', ''))}"
                first_service.save()

                logger.info(f"Updated existing service (after cleanup): {name}")
                imported += 1
                continue

            # Create or update PublicService object
            try:
                service, created = PublicService.objects.update_or_create(
                    name=name,
                    service_type=PublicService.ServiceType.CITY_HALL,
                    defaults={
                        'address': fix_encoding(item.get('Adresse', '')),
                        'postal_code': str(item.get('CodePostal', '')),
                        'city': fix_encoding(city_name),
                        'phone': fix_encoding(item.get('Téléphone', '')),
                        'email': fix_encoding(item.get('Email', '')),
                        'website': fix_encoding(item.get('Url', '')),
                        'latitude': latitude,
                        'longitude': longitude,
                        'notes': f"Code INSEE: {item.get('codeInsee', '')}, Mise à jour: {fix_encoding(item.get('dateMiseAJour', ''))}"
                    }
                )
            except Exception as e:
                # If there's still an error, try to create a new record with a slightly modified name
                try:
                    code_insee = item.get('codeInsee', '')
                    modified_name = f"{name} (INSEE: {code_insee})"

                    service = PublicService.objects.create(
                        name=modified_name,
                        service_type=PublicService.ServiceType.CITY_HALL,
                        address=fix_encoding(item.get('Adresse', '')),
                        postal_code=str(item.get('CodePostal', '')),
                        city=fix_encoding(city_name),
                        phone=fix_encoding(item.get('Téléphone', '')),
                        email=fix_encoding(item.get('Email', '')),
                        website=fix_encoding(item.get('Url', '')),
                        latitude=latitude,
                        longitude=longitude,
                        notes=f"Code INSEE: {code_insee}, Mise à jour: {fix_encoding(item.get('dateMiseAJour', ''))}"
                    )
                    created = True
                    logger.info(f"Created service with modified name: {modified_name}")
                except Exception as inner_e:
                    # If that also fails, re-raise the original exception
                    raise e

            imported += 1
            logger.info(f"{'Created' if created else 'Updated'} service: {name}")

        except Exception as e:
            logger.error(f"Error importing mairie: {str(e)}, data: {item}")
            errors += 1

    return {
        "success": True,
        "message": f"Imported {imported} mairies with {errors} errors",
        "imported": imported,
        "errors": errors
    }

def import_pharmacies_1_data(file_path):
    """
    Import data from liste-des-pharmacies-1.json file
    """
    data = load_json_file(file_path)
    if not data:
        return {"success": False, "message": "Failed to load data file", "imported": 0, "errors": 0}

    imported = 0
    errors = 0

    for item in data:
        try:
            print(item.get('pharmacie', ''))
            # Extract data from JSON
            name = item.get('pharmacie', '')
            if not name:
                logger.warning(f"Skipping record with no name: {item}")
                errors += 1
                continue

            # Parse opening hours
            opening_hour = '09:00:00'
            closing_hour = '19:00:00'
            horaires = item.get('horaires_d_ouverture', '')

            # Handle latitude and longitude - convert empty strings to None
            latitude = item.get('latitude')
            if latitude == '' or latitude is None:
                latitude = None
            else:
                try:
                    latitude = float(latitude)
                except (ValueError, TypeError):
                    latitude = None

            longitude = item.get('longitude')
            if longitude == '' or longitude is None:
                longitude = None
            else:
                try:
                    longitude = float(longitude)
                except (ValueError, TypeError):
                    longitude = None

            # Si les coordonnées sont manquantes, essayer de les obtenir par géocodage
            if (latitude is None or longitude is None) and item.get('adresse'):
                # Attendre un peu pour respecter le rate limiting
                wait_for_rate_limit()

                # Essayer de géocoder l'adresse
                address = item.get('adresse', '')
                quartier = item.get('quartier', '')

                logger.info(f"Tentative de géocodage pour {name}: {address}, {quartier}")
                geo_lat, geo_lon = geocode_address(address, city=quartier)

                if geo_lat and geo_lon:
                    latitude = geo_lat
                    longitude = geo_lon
                    logger.info(f"Géocodage réussi pour {name}: {latitude}, {longitude}")
                else:
                    logger.warning(f"Échec du géocodage pour {name}")

                # Attendre entre les requêtes pour respecter le rate limiting
                wait_for_rate_limit()

            # Create or update PublicService object
            try:
                service, created = PublicService.objects.update_or_create(
                    name=name,
                    service_type=PublicService.ServiceType.PHARMACY,
                    defaults={
                        'address': item.get('adresse', ''),
                        'postal_code': '',  # Not provided in this dataset
                        'city': item.get('quartier', ''),
                        'phone': item.get('contact', ''),
                        'website': item.get('web', ''),
                        'latitude': latitude,
                        'longitude': longitude,
                        'opening_hour': opening_hour,
                        'closing_hour': closing_hour,
                        'notes': f"Horaires: {horaires}"
                    }
                )
            except Exception as e:
                # If there's an error, try to create a new record with a slightly modified name
                try:
                    modified_name = f"{name} ({item.get('quartier', 'unknown')})"

                    service = PublicService.objects.create(
                        name=modified_name,
                        service_type=PublicService.ServiceType.PHARMACY,
                        address=item.get('adresse', ''),
                        postal_code='',  # Not provided in this dataset
                        city=item.get('quartier', ''),
                        phone=item.get('contact', ''),
                        website=item.get('web', ''),
                        latitude=latitude,
                        longitude=longitude,
                        opening_hour=opening_hour,
                        closing_hour=closing_hour,
                        notes=f"Horaires: {horaires}"
                    )
                    created = True
                    logger.info(f"Created pharmacy with modified name: {modified_name}")
                except Exception as inner_e:
                    # If that also fails, re-raise the original exception
                    raise e

            imported += 1
            logger.info(f"{'Created' if created else 'Updated'} service: {name}")
            print(f"{'Created' if created else 'Updated'} service: {name}")
        except Exception as e:
            logger.error(f"Error importing pharmacy: {str(e)}, data: {item}")
            errors += 1

    return {
        "success": True,
        "message": f"Imported {imported} pharmacies with {errors} errors",
        "imported": imported,
        "errors": errors
    }

def import_pharmacies_2_data(file_path):
    """
    Import data from liste-des-pharmacies-2.json file
    """
    data = load_json_file(file_path)
    if not data:
        return {"success": False, "message": "Failed to load data file", "imported": 0, "errors": 0}

    imported = 0
    errors = 0

    for item in data:
        try:
            print(item.get('Pharmacie', ''))
            # Extract data from JSON
            name = item.get('Pharmacie', '')
            if not name:
                logger.warning(f"Skipping record with no name: {item}")
                errors += 1
                continue

            # Essayer de géocoder l'adresse si elle existe
            latitude = None
            longitude = None

            if item.get('Adresse'):
                # Attendre un peu pour respecter le rate limiting
                wait_for_rate_limit()

                # Essayer de géocoder l'adresse
                address = item.get('Adresse', '')
                postal_code = str(item.get('CP', ''))
                city = item.get('VILLE', '')

                logger.info(f"Tentative de géocodage pour {name}: {address}, {postal_code}, {city}")
                geo_lat, geo_lon = geocode_address(address, postal_code, city)

                if geo_lat and geo_lon:
                    latitude = geo_lat
                    longitude = geo_lon
                    logger.info(f"Géocodage réussi pour {name}: {latitude}, {longitude}")
                else:
                    logger.warning(f"Échec du géocodage pour {name}")

                # Attendre entre les requêtes pour respecter le rate limiting
                wait_for_rate_limit()

            # Create or update PublicService object
            try:
                service, created = PublicService.objects.update_or_create(
                    name=name,
                    service_type=PublicService.ServiceType.PHARMACY,
                    defaults={
                        'address': item.get('Adresse', ''),
                        'postal_code': str(item.get('CP', '')),
                        'city': item.get('VILLE', ''),
                        'phone': item.get('Téléphone', ''),
                        'latitude': latitude,
                        'longitude': longitude,
                        'notes': f"Titulaire: {item.get('Titulaire', '')}, Garde: {item.get('GARDES DE JOURS 2015', '')}"
                    }
                )
            except Exception as e:
                # If there's an error, try to create a new record with a slightly modified name
                try:
                    modified_name = f"{name} ({item.get('VILLE', 'unknown')})"

                    service = PublicService.objects.create(
                        name=modified_name,
                        service_type=PublicService.ServiceType.PHARMACY,
                        address=item.get('Adresse', ''),
                        postal_code=str(item.get('CP', '')),
                        city=item.get('VILLE', ''),
                        phone=item.get('Téléphone', ''),
                        notes=f"Titulaire: {item.get('Titulaire', '')}, Garde: {item.get('GARDES DE JOURS 2015', '')}"
                    )
                    created = True
                    logger.info(f"Created pharmacy with modified name: {modified_name}")
                except Exception as inner_e:
                    # If that also fails, re-raise the original exception
                    raise e

            imported += 1
            logger.info(f"{'Created' if created else 'Updated'} service: {name}")

        except Exception as e:
            logger.error(f"Error importing pharmacy: {str(e)}, data: {item}")
            errors += 1

    return {
        "success": True,
        "message": f"Imported {imported} pharmacies with {errors} errors",
        "imported": imported,
        "errors": errors
    }

def import_pharmacies_3_data(file_path):
    """
    Import data from liste-des-pharmacies-3.json file
    """
    data = load_json_file(file_path)
    if not data:
        return {"success": False, "message": "Failed to load data file", "imported": 0, "errors": 0}

    imported = 0
    errors = 0

    # Since we don't have the exact structure of this file, we'll implement a generic approach
    # that tries to adapt to whatever structure is found
    for item in data:
        try:
            # Try to extract name from various possible fields
            name = None
            for field in ['pharmacie', 'Pharmacie', 'nom', 'Nom', 'name', 'Name']:
                if field in item and item[field]:
                    name = item[field]
                    break

            if not name:
                logger.warning(f"Skipping record with no identifiable name: {item}")
                errors += 1
                continue
            print(name)

            # Try to extract address from various possible fields
            address = ''
            for field in ['adresse', 'Adresse', 'address', 'Address']:
                if field in item and item[field]:
                    address = item[field]
                    break

            # Try to extract postal code from various possible fields
            postal_code = ''
            for field in ['code_postal', 'CodePostal', 'CP', 'postal_code', 'PostalCode']:
                if field in item and item[field]:
                    postal_code = str(item[field])
                    break

            # Try to extract city from various possible fields
            city = ''
            for field in ['ville', 'Ville', 'VILLE', 'city', 'City']:
                if field in item and item[field]:
                    city = item[field]
                    break

            # Try to extract phone from various possible fields
            phone = ''
            for field in ['telephone', 'Telephone', 'Téléphone', 'phone', 'Phone', 'contact']:
                if field in item and item[field]:
                    phone = item[field]
                    break

            # Try to extract coordinates
            latitude = None
            longitude = None
            for lat_field in ['latitude', 'Latitude', 'lat', 'Lat']:
                if lat_field in item and item[lat_field]:
                    try:
                        latitude = float(item[lat_field])
                        break
                    except (ValueError, TypeError):
                        pass

            for lng_field in ['longitude', 'Longitude', 'lng', 'Lng', 'lon', 'Lon']:
                if lng_field in item and item[lng_field]:
                    try:
                        longitude = float(item[lng_field])
                        break
                    except (ValueError, TypeError):
                        pass

            # Si les coordonnées sont manquantes, essayer de les obtenir par géocodage
            if (latitude is None or longitude is None) and address:
                # Attendre un peu pour respecter le rate limiting
                wait_for_rate_limit()

                logger.info(f"Tentative de géocodage pour {name}: {address}, {postal_code}, {city}")
                geo_lat, geo_lon = geocode_address(address, postal_code, city)

                if geo_lat and geo_lon:
                    latitude = geo_lat
                    longitude = geo_lon
                    logger.info(f"Géocodage réussi pour {name}: {latitude}, {longitude}")
                else:
                    logger.warning(f"Échec du géocodage pour {name}")

                # Attendre entre les requêtes pour respecter le rate limiting
                wait_for_rate_limit()

            # Create or update PublicService object
            try:
                service, created = PublicService.objects.update_or_create(
                    name=name,
                    service_type=PublicService.ServiceType.PHARMACY,
                    defaults={
                        'address': address,
                        'postal_code': postal_code,
                        'city': city,
                        'phone': phone,
                        'latitude': latitude,
                        'longitude': longitude,
                        'notes': f"Imported from pharmacies-3 dataset"
                    }
                )
            except Exception as e:
                # If there's an error, try to create a new record with a slightly modified name
                try:
                    modified_name = f"{name} ({city or 'unknown'})"

                    service = PublicService.objects.create(
                        name=modified_name,
                        service_type=PublicService.ServiceType.PHARMACY,
                        address=address,
                        postal_code=postal_code,
                        city=city,
                        phone=phone,
                        latitude=latitude,
                        longitude=longitude,
                        notes=f"Imported from pharmacies-3 dataset"
                    )
                    created = True
                    logger.info(f"Created pharmacy with modified name: {modified_name}")
                except Exception as inner_e:
                    # If that also fails, re-raise the original exception
                    raise e

            imported += 1
            logger.info(f"{'Created' if created else 'Updated'} service: {name}")

        except Exception as e:
            logger.error(f"Error importing pharmacy: {str(e)}, data: {item}")
            errors += 1

    return {
        "success": True,
        "message": f"Imported {imported} pharmacies with {errors} errors",
        "imported": imported,
        "errors": errors
    }

def wait_for_rate_limit(delay=None):
    """
    Attend un certain temps entre les requêtes pour respecter le rate limiting

    Args:
        delay: Délai spécifique à attendre. Si None, utilise RATE_LIMIT_DELAY avec un jitter
    """
    if delay is None:
        # Ajouter un jitter pour éviter les requêtes synchronisées
        jitter_factor = 1 + random.uniform(-JITTER, JITTER)
        delay = RATE_LIMIT_DELAY * jitter_factor

    logger.debug(f"Attente de {delay:.2f} secondes pour respecter le rate limit")
    time.sleep(delay)

def make_api_request(url, method='GET', params=None, headers=None, data=None, json_data=None):
    """
    Effectue une requête API avec gestion du rate limiting

    Args:
        url: URL de la requête
        method: Méthode HTTP (GET, POST, etc.)
        params: Paramètres de requête
        headers: En-têtes HTTP
        data: Données à envoyer (form data)
        json_data: Données JSON à envoyer

    Returns:
        La réponse de l'API ou None en cas d'échec après plusieurs tentatives
    """
    retry_count = 0
    delay = RATE_LIMIT_DELAY

    while retry_count <= MAX_RETRIES:
        try:
            # Attendre avant de faire la requête pour respecter le rate limit
            if retry_count > 0:
                wait_for_rate_limit(delay)

            response = requests.request(
                method=method,
                url=url,
                params=params,
                headers=headers,
                data=data,
                json=json_data,
                timeout=30  # Timeout de 30 secondes
            )

            # Vérifier si on a atteint une limite de rate
            if response.status_code in (429, 403):  # 429 Too Many Requests, 403 peut aussi indiquer un rate limit
                retry_count += 1
                delay = RATE_LIMIT_DELAY * (BACKOFF_FACTOR ** retry_count)
                logger.warning(f"Rate limit atteint. Attente de {delay:.2f} secondes avant réessai ({retry_count}/{MAX_RETRIES})")
                continue

            # Pour les autres codes d'erreur, on peut aussi réessayer
            if response.status_code >= 500:
                retry_count += 1
                delay = RATE_LIMIT_DELAY * (BACKOFF_FACTOR ** retry_count)
                logger.warning(f"Erreur serveur {response.status_code}. Attente de {delay:.2f} secondes avant réessai ({retry_count}/{MAX_RETRIES})")
                continue

            # Si on arrive ici, la requête a réussi ou a échoué de manière définitive
            response.raise_for_status()  # Lève une exception pour les codes d'erreur HTTP
            return response

        except requests.exceptions.RequestException as e:
            retry_count += 1
            if retry_count <= MAX_RETRIES:
                delay = RATE_LIMIT_DELAY * (BACKOFF_FACTOR ** retry_count)
                logger.warning(f"Erreur de requête: {str(e)}. Attente de {delay:.2f} secondes avant réessai ({retry_count}/{MAX_RETRIES})")
            else:
                logger.error(f"Échec de la requête après {MAX_RETRIES} tentatives: {str(e)}")
                return None

    return None

def geocode_address(address, postal_code=None, city=None):
    """
    Géocode une adresse en utilisant une API externe avec gestion du rate limiting

    Args:
        address: Adresse à géocoder
        postal_code: Code postal (optionnel)
        city: Ville (optionnel)

    Returns:
        Un tuple (latitude, longitude) ou (None, None) en cas d'échec
    """
    # Construire l'adresse complète
    full_address = address
    if postal_code:
        full_address += f", {postal_code}"
    if city:
        full_address += f", {city}"
    full_address += ", France"  # Ajouter le pays pour améliorer la précision

    # Utiliser l'API de géocodage (exemple avec Nominatim)
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": full_address,
        "format": "json",
        "limit": 1,
        "addressdetails": 1
    }
    headers = {
        "User-Agent": "MediaApp/1.0"  # Nominatim exige un User-Agent personnalisé
    }

    # Faire la requête avec gestion du rate limiting
    response = make_api_request(url, params=params, headers=headers)

    if response and response.status_code == 200:
        data = response.json()
        if data and len(data) > 0:
            return float(data[0]["lat"]), float(data[0]["lon"])

    return None, None

def run_import_in_thread(import_function, file_path):
    """
    Run the import function in a separate thread
    """
    def wrapper():
        try:
            result = import_function(file_path)
            logger.info(f"Import completed: {result}")
        except Exception as e:
            logger.error(f"Error in import thread: {str(e)}")

    thread = threading.Thread(target=wrapper)
    thread.daemon = True
    thread.start()
    return thread
