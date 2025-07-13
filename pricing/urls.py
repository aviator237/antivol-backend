from django.urls import path

from .views import *

app_name = "pricing"
urlpatterns = [
    # URLs pour les utilisateurs classiques
    path('', pricing, name='index'),
    path('upgrade_plan/', upgrade_plan, name='upgrade_plan'),
    path('subscribe/<int:product_id>/', subscribe, name='subscribe'),
    path('downgrade/<int:product_id>/', downgrade, name='downgrade'),
    path('create_checkout_session/<int:plan_id>/', create_checkout_session, name='create_checkout_session'),
    path('success/', success, name='success'),
    path('cancel/', cancel, name='cancel'),
    path('stripe_portal/', stripe_portal, name='stripe_portal'),

    # URLs pour les entreprises
    path('company/', company_pricing, name='company_pricing'),
    path('company/plans/', company_plans, name='company_plans'),
    path('company/subscribe/<int:plan_id>/', company_subscribe, name='company_subscribe'),
    path('company/success/', company_success, name='company_success'),
    path('company/cancel/', company_cancel, name='company_cancel'),
    path('company/cancel_subscription/', cancel_subscription, name='cancel_subscription'),

    # Webhook Stripe
    path('webhook/', stripe_webhook, name='stripe_webhook'),
]

# stripe listen --forward-to 127.0.0.1:8000/pricing/webhook --skip-verify
