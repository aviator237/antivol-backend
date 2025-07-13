from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Product, PlanType, Plan, Payment, Subscription, StatusType
from account.models import Profil, UserRole
from django.contrib.auth.models import User
from account.views import get_user_photos_directory_size
from django.contrib.auth.decorators import login_required
from django.core.handlers.wsgi import WSGIRequest
import stripe
from django.conf import settings
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .utils import get_stripe_allowed_ips
import threading
from datetime import datetime

import logging

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def pricing(request):
    try:
        profile = Profil.objects.get(owner=request.user)
        if profile.is_company_owner():
            # messages.error(request, "Vous n'êtes pas associé à une entreprise.")
            return redirect('pricing:company_pricing')
    except Profil.DoesNotExist:
        messages.error(request, "Profil utilisateur non trouvé.")
        return redirect('/account')

    user = request.user
    free_product = Product.objects.get(type=PlanType.FREE.value[0])
    try:
        user.profil.plan = Plan.objects.get(profil=user.profil)
        user_product = user.profil.plan.product
    except Plan.DoesNotExist:
        user_product = free_product

    user.profil = Profil.objects.get(owner=user)
    total_size = get_user_photos_directory_size(request.user)
    remaining_storage = user_product.storage - total_size
    used_percentage = (total_size / user_product.storage) * 100

    if used_percentage < 50:
        color = '#4caf50'  # Green
    elif used_percentage < 75:
        color = '#ffeb3b'  # Yellow
    else:
        color = '#f44336'  # Red

    pregress_bar = f'''<div id="progressContainer">
            <div id="progressBar" style="width: {used_percentage:2f}%; background-color: {color};"></div>
            <span class="percentage">{round(used_percentage, 2)}%</span>
        </div>'''
    context = {
        'title': 'Plans de tarification',
        'user': user,
        'user_product': user_product,
        'free_product': free_product,
        'remaining_storage': remaining_storage,
        'pregress_bar': pregress_bar,
        'used_percentage': used_percentage,
    }

    if user.profil.stripe_customer_id:
        context["is_stripe_customer"] = True

    return render(request, 'pricing/index.html', context)

@login_required
def stripe_portal(request: WSGIRequest):
    user_profil = Profil.objects.get(owner=request.user)
    if user_profil.stripe_customer_id:
        portal_session = stripe.billing_portal.Session.create(
        customer=user_profil.stripe_customer_id,
        return_url=request.build_absolute_uri(f'/pricing/'),
        )
        return redirect(portal_session.get("url"))
    else:
        messages.error(request, "Il semble que vous n'avez pas encore souscrit à un abonnement")
        return redirect("pricing:index")



@login_required
def downgrade(request: WSGIRequest, product_id):
    user = request.user
    new_product = get_object_or_404(Product, id=product_id)
    user.profil = Profil.objects.get(owner=user)

    try:
        user.profil.plan = Plan.objects.get(profil=user.profil)
        user_product = user.profil.plan.product
    except Plan.DoesNotExist:
        user_product = Product.objects.get(type=PlanType.FREE.value[0])
    confirm = request.GET.get("confirm")
    if confirm is not None and confirm =="yes":
        if not new_product.is_free():
            return redirect("pricing:subscribe", product_id)
        else:
            cancel_user_subscription(user)
            user.profil.plan = None
            user.profil.stripe_customer_id = None
            user.profil.save()
            return redirect("pricing:index")

    total_size = get_user_photos_directory_size(request.user)
    remaining_storage = user_product.storage - total_size
    used_percentage = (total_size / user_product.storage) * 100
    print(new_product.storage)
    print(total_size)
    print(":::::::::::::::::::::::::::::::::::::::::::::::::::::")
    context = {
        'title': 'Downgrade plan',
        'user': user,
        'new_product': new_product,
        'can_downgrade': total_size <= new_product.storage,
        'user_product': user_product,
        'remaining_storage': remaining_storage,
        'used_percentage': used_percentage,
    }
    return render(request, 'pricing/downgrade.html', context)

@login_required
def upgrade_plan(request: WSGIRequest):
    user = request.user
    free_product = Product.objects.get(type=PlanType.FREE.value[0])
    try:
        user.profil.plan = Plan.objects.get(profil=user.profil)
        user_product = user.profil.plan.product
    except Plan.DoesNotExist:
        user_product = free_product

    products = Product.objects.filter(type=PlanType.STANDARD.value[0])
    context = {
        "title": "Upgrade Plan",
        "products": products,
        "user_product": user_product,
        "free_product": free_product,
    }
    return render(request, "pricing/upgrade_plan.html", context)

@login_required
def subscribe(request: WSGIRequest, product_id):
    product = get_object_or_404(Product, id=product_id)
    plans = product.get_plans()
    context = {
        "title": "Souscrire à un plan",
        "product": product,
        "plans": plans,
    }
    return render(request, "pricing/subscribe.html", context)

@login_required
def create_checkout_session(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    user = request.user
    try:
        cancel_user_subscription(user)
        # user.profil.stripe_customer_id = None
        # user.profil.save()
    except Subscription.DoesNotExist:
        pass

    # new_souscription  = Subscription.objects.create(
    #     user=user,
    #     plan=plan,
    # )
    line_items=[
            {
                'price_data': {
                    'currency': plan.currency,
                    'product_data': {
                        'name': plan.product.name,
                    },
                    'unit_amount': plan.amount * 100,  # Amount in cents
                    'recurring': {
                        'interval': plan.interval,
                        'interval_count': plan.interval_count,
                    },
                },
                'quantity': 1,
            },
        ]

    if not user.profil.stripe_customer_id:
        customer = stripe.Customer.create(
            # phone=user.username,
            name=f"{user.first_name} {user.last_name}",
        )
        user.profil.stripe_customer_id = customer.id
    user.profil.plan = plan
    user.profil.save()

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        customer=user.profil.stripe_customer_id,
        line_items=line_items,
        mode='subscription',
        success_url=request.build_absolute_uri(f'/pricing/success/'),
        cancel_url=request.build_absolute_uri('/pricing/cancel/'),
    )
    logger.debug(session)
    print(session)
    # new_souscription.stripe_session_id = session.id
    # new_souscription.save()
    return redirect(session.url)



def success(request):
    messages.success(request, "Votre souscription a réussie")
    return redirect("pricing:upgrade_plan")

def cancel(request):
    request.user.profil.plan = None
    request.user.profil.save()
    messages.error(request, "Votre souscription a échoué")
    return redirect("pricing:upgrade_plan")

@require_POST
@csrf_exempt
def stripe_webhook(request):
    if not settings.DEBUG:
        allowed_ips = get_stripe_allowed_ips()
        request_ip = request.META.get('REMOTE_ADDR')
        if request_ip not in allowed_ips:
            logger.debug("IP non reconnu***************************")
            return HttpResponse(status=403)

    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        logger.debug(e)
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.debug(e)
        return HttpResponse(status=400)

    # Handle the event in a separate thread
    event_type = event['type']
    event_data = event['data']['object']
    print(event_type)
    threading.Thread(target=process_stripe_event, args=(event_type, event_data)).start()

    return HttpResponse(status=200)

def process_stripe_event(event_type, event_data):
    logger.debug(event_type)
    logger.debug(event_data)
    if event_type == 'invoice.payment_succeeded':
        print(event_type)
        print(event_data)
        handle_invoice_payment_succeeded(event_data)
    elif event_type == 'invoice.payment_failed':
        handle_invoice_payment_failed(event_data)
    else:
        return

def handle_invoice_payment_succeeded(invoice):
    user_profil = Profil.objects.get(stripe_customer_id=invoice['customer'])
    try:
        subscription = Subscription.objects.get(stripe_subscription_id=invoice['subscription'])
    except Subscription.DoesNotExist:
        subscription  = Subscription.objects.create(
        user=user_profil.owner,
        plan=user_profil.plan,
        status=StatusType.ACTIVE.value[0],
        stripe_subscription_id=invoice['subscription']
        )
    created = datetime.fromtimestamp(invoice['created'])
    period_start = datetime.fromtimestamp(invoice['period_start'])
    period_end = datetime.fromtimestamp(invoice['period_end'])
    Payment.objects.create(
        user=user_profil.owner,
        subscription=subscription,
        stripe_payment_intent_id=invoice['payment_intent'],
        amount=invoice['amount_paid'] / 100,  # Convert from cents to euros
        currency=invoice['currency'],
        status=invoice['status'],
        billing_reason=invoice.get('billing_reason'),
        created=created,
        customer_email=invoice.get('customer_email'),
        hosted_invoice_url=invoice.get('hosted_invoice_url'),
        invoice_pdf=invoice.get('invoice_pdf'),
        stripe_invoice_id=invoice.get('id'),
        paid=invoice.get('paid'),
        period_end=period_end,
        period_start=period_start,
        amount_due=invoice.get('amount_due') / 100 if invoice.get('amount_due') else None,
        amount_paid=invoice.get('amount_paid') / 100 if invoice.get('amount_paid') else None,
    )

    # Réactiver l'entreprise si elle était désactivée
    if user_profil.company and subscription.plan.product.type == PlanType.COMPANY_CATALOG.value[0]:
        if not user_profil.company.is_active and not user_profil.company.is_banned:
            user_profil.company.reactivate()
            logger.info(f"Entreprise {user_profil.company.name} (ID: {user_profil.company.id}) réactivée suite à la souscription d'un abonnement")

def handle_invoice_payment_failed(invoice):
    user_profil = Profil.objects.get(stripe_customer_id=invoice['customer'])
    try:
        subscription = Subscription.objects.get(stripe_subscription_id=invoice['subscription'])
    except Subscription.DoesNotExist:
        subscription  = Subscription.objects.create(
        user=user_profil.owner,
        plan=user_profil.plan,
        status=StatusType.ACTIVE.value[0],
        stripe_subscription_id=invoice['subscription']
        )
    created = datetime.fromtimestamp(invoice['created'])
    period_start = datetime.fromtimestamp(invoice['period_start'])
    period_end = datetime.fromtimestamp(invoice['period_end'])
    Payment.objects.create(
        user=user_profil.owner,
        subscription=subscription,
        stripe_payment_intent_id=invoice['payment_intent'],
        amount=invoice['amount_paid'] / 100,  # Convert from cents to euros
        currency=invoice['currency'],
        status=invoice['status'],
        billing_reason=invoice.get('billing_reason'),
        created=created,
        customer_email=invoice.get('customer_email'),
        hosted_invoice_url=invoice.get('hosted_invoice_url'),
        invoice_pdf=invoice.get('invoice_pdf'),
        stripe_invoice_id=invoice.get('id'),
        paid=invoice.get('paid'),
        period_end=period_end,
        period_start=period_start,
        amount_due=invoice.get('amount_due') / 100 if invoice.get('amount_due') else None,
        amount_paid=invoice.get('amount_paid') / 100 if invoice.get('amount_paid') else None,
    )



def cancel_user_subscription(user: User):
    try:
        current_subscription = Subscription.objects.get(user=user, status=StatusType.ACTIVE.value[0])
        stripe.Subscription.delete(current_subscription.stripe_subscription_id)
        current_subscription.status = StatusType.CANCELED.value[0]
        current_subscription.save()
    except Exception as e:
        print(e)


# Vues pour les abonnements d'entreprise
@login_required
def company_pricing(request):
    """Vue pour afficher les options d'abonnement pour les entreprises"""
    user = request.user

    # Vérifier si l'utilisateur est un administrateur d'entreprise
    try:
        profile = Profil.objects.get(owner=user)
        if profile.role != UserRole.COMPANY_OWNER:
            messages.error(request, "Cette page est réservée aux administrateurs d'entreprise.")
            return redirect('/account/')
    except Profil.DoesNotExist:
        messages.error(request, "Profil utilisateur non trouvé.")
        return redirect('/account/')

    # Récupérer le produit pour les catalogues d'entreprise
    try:
        company_catalog_product = Product.objects.get(type=PlanType.COMPANY_CATALOG.value[0])
    except Product.DoesNotExist:
        messages.error(request, "Les plans d'abonnement pour les entreprises ne sont pas encore disponibles.")
        return redirect('/company/')

    # Récupérer l'abonnement actuel de l'entreprise
    try:
        current_subscription = Subscription.objects.get(
            user=user,
            status=StatusType.ACTIVE.value[0],
            plan__product__type=PlanType.COMPANY_CATALOG.value[0]
        )
        current_plan = current_subscription.plan
    except Subscription.DoesNotExist:
        current_plan = None

    context = {
        'title': 'Abonnements pour la publication de catalogues',
        'user': user,
        'company_catalog_product': company_catalog_product,
        'current_plan': current_plan,
        'is_stripe_customer': bool(user.profil.stripe_customer_id),
    }

    return render(request, 'pricing/company_pricing.html', context)


@login_required
def company_plans(request):
    """Vue pour afficher les différents plans d'abonnement pour les entreprises"""
    user = request.user

    # Vérifier si l'utilisateur est un administrateur d'entreprise
    try:
        profile = Profil.objects.get(owner=user)
        if profile.role != UserRole.COMPANY_OWNER:
            messages.error(request, "Cette page est réservée aux administrateurs d'entreprise.")
            return redirect('/account/')
    except Profil.DoesNotExist:
        messages.error(request, "Profil utilisateur non trouvé.")
        return redirect('/account/')

    # Récupérer le produit pour les catalogues d'entreprise
    try:
        company_catalog_product = Product.objects.get(type=PlanType.COMPANY_CATALOG.value[0])
        plans = company_catalog_product.get_plans()
    except Product.DoesNotExist:
        messages.error(request, "Les plans d'abonnement pour les entreprises ne sont pas encore disponibles.")
        return redirect('/company/')

    # Récupérer l'abonnement actuel de l'entreprise
    try:
        current_subscription = Subscription.objects.get(
            user=user,
            status=StatusType.ACTIVE.value[0],
            plan__product__type=PlanType.COMPANY_CATALOG.value[0]
        )
        current_plan = current_subscription.plan
    except Subscription.DoesNotExist:
        current_plan = None

    context = {
        'title': 'Plans d\'abonnement pour la publication de catalogues',
        'user': user,
        'company_catalog_product': company_catalog_product,
        'plans': plans,
        'current_plan': current_plan,
    }

    return render(request, 'pricing/company_plans.html', context)


@login_required
def company_subscribe(request, plan_id):
    """Vue pour souscrire à un plan d'abonnement pour les entreprises"""
    user = request.user

    # Vérifier si l'utilisateur est un administrateur d'entreprise
    try:
        profile = Profil.objects.get(owner=user)
        if profile.role != UserRole.COMPANY_OWNER:
            messages.error(request, "Cette page est réservée aux administrateurs d'entreprise.")
            return redirect('/account/')
    except Profil.DoesNotExist:
        messages.error(request, "Profil utilisateur non trouvé.")
        return redirect('/account/')

    # Récupérer le plan
    plan = get_object_or_404(Plan, id=plan_id)

    # Vérifier que le plan est bien un plan pour les catalogues d'entreprise
    if plan.product.type != PlanType.COMPANY_CATALOG.value[0]:
        messages.error(request, "Ce plan n'est pas destiné aux entreprises.")
        return redirect('pricing:company_plans')

    # Annuler l'abonnement actuel s'il existe
    try:
        cancel_user_subscription(user)
    except Subscription.DoesNotExist:
        pass

    # Préparer les éléments de ligne pour Stripe
    line_items = [
        {
            'price_data': {
                'currency': plan.currency,
                'product_data': {
                    'name': f"Abonnement Catalogue Entreprise - {plan.get_interval_display()}",
                    'description': plan.product.description,
                },
                'unit_amount': plan.amount * 100,  # Montant en centimes
                'recurring': {
                    'interval': plan.interval,
                    'interval_count': plan.interval_count,
                },
            },
            'quantity': 1,
        },
    ]

    # Créer ou récupérer le client Stripe
    if not user.profil.stripe_customer_id:
        customer = stripe.Customer.create(
            email=user.email,
            name=f"{user.first_name} {user.last_name}",
            metadata={
                'user_id': user.id,
                'company_name': profile.company.name if profile.company else '',
            }
        )
        user.profil.stripe_customer_id = customer.id

    user.profil.plan = plan
    user.profil.save()

    # Créer la session de paiement Stripe
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        customer=user.profil.stripe_customer_id,
        line_items=line_items,
        mode='subscription',
        success_url=request.build_absolute_uri('/pricing/company/success/'),
        cancel_url=request.build_absolute_uri('/pricing/company/cancel/'),
        metadata={
            'plan_id': plan.id,
            'user_id': user.id,
        }
    )

    return redirect(session.url)


@login_required
def company_success(request):
    """Vue pour afficher la page de succès après la souscription"""
    messages.success(request, "Votre souscription a été réalisée avec succès. Vous pouvez maintenant publier vos catalogues.")
    return redirect('pricing:company_pricing')


@login_required
def company_cancel(request):
    """Vue pour afficher la page d'annulation après l'échec de la souscription"""
    request.user.profil.plan = None
    request.user.profil.save()
    messages.error(request, "Votre souscription a été annulée ou a échoué.")
    return redirect('pricing:company_plans')


@login_required
def cancel_subscription(request):
    """Vue pour annuler un abonnement existant"""
    user = request.user

    # Vérifier si l'utilisateur est un administrateur d'entreprise
    try:
        profile = Profil.objects.get(owner=user)
        if profile.role != UserRole.COMPANY_OWNER:
            messages.error(request, "Cette action est réservée aux administrateurs d'entreprise.")
            return redirect('/account/')
    except Profil.DoesNotExist:
        messages.error(request, "Profil utilisateur non trouvé.")
        return redirect('/account/')

    # Annuler l'abonnement actuel
    try:
        cancel_user_subscription(user)
        messages.success(request, "Votre abonnement a été annulé avec succès. Il restera actif jusqu'à la fin de la période de facturation en cours.")
    except Exception as e:
        messages.error(request, f"Une erreur s'est produite lors de l'annulation de votre abonnement: {str(e)}")

    return redirect('pricing:company_pricing')


