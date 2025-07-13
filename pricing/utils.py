import requests
from django.core.cache import cache

STRIPE_IPS_URL = "https://stripe.com/files/ips/ips_webhooks.json"
CACHE_TIMEOUT = 60 * 60  # Cache for 1 hour

def get_stripe_allowed_ips():
    allowed_ips = cache.get('stripe_allowed_ips')
    if not allowed_ips:
        response = requests.get(STRIPE_IPS_URL)
        if response.status_code == 200:
            allowed_ips = response.json().get('WEBHOOKS', [])
            cache.set('stripe_allowed_ips', allowed_ips, CACHE_TIMEOUT)
        else:
            allowed_ips = []
    return allowed_ips
