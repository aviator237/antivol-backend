from rest_framework.throttling import SimpleRateThrottle

class BurstRateThrottle(SimpleRateThrottle):
    scope = 'burst'
    rate = '3/second'

class SustainedRateThrottle(SimpleRateThrottle):
    scope = 'sustained'
    rate = '20/10s'  # 20 requêtes en 10 secondes

class MinuteRateThrottle(SimpleRateThrottle):
    scope = 'minute'
    rate = '100/minute'