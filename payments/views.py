from django.urls import reverse
import stripe
from django.conf import settings
from django.shortcuts import render, redirect

stripe.api_key = settings.STRIPE_SECRET_KEY

def create_checkout_session(request):
    # Create a new Checkout Session
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[
            {
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Product Name',
                    },
                    'unit_amount': 1000,  # Amount in cents
                },
                'quantity': 1,
            },
        ],
        mode='payment',
        success_url=request.build_absolute_uri(reverse('payments:success')),
        cancel_url=request.build_absolute_uri(reverse('payments:cancel')),
    )

    return redirect(session.url)

def success(request):
    return render(request, 'payments/success.html')

def cancel(request):
    return render(request, 'payments/cancel.html')