from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Product, Plan, PlanType, Subscription
import stripe
from django.conf import settings
stripe.api_key = settings.STRIPE_SECRET_KEY

@receiver(post_save, sender=Product)
def create_or_update_stripe_product(sender, instance, created, **kwargs):
    if instance.type != PlanType.FREE.value[0]:
        try:
            product_data = {
                    "name": instance.name,
                }
            if instance.description:
                product_data["description"] = instance.description
            if created:
                product = stripe.Product.create(**product_data)
                instance.stripe_product_id = product.id
                instance.save()
            else:
                stripe.Product.modify(
                    instance.stripe_product_id,
                    **product_data
                )
        except Exception as e:
            print(e)

# @receiver(post_delete, sender=Product)
# def delete_stripe_product(sender, instance, **kwargs):
#     if instance.type != PlanType.FREE.value[0]:
#         try:
#             stripe.Product.delete(instance.stripe_product_id)
#         except Exception as e:
#             print(e)

@receiver(post_save, sender=Plan)
def create_or_update_stripe_plan(sender, instance, created, **kwargs):
    try:
        if created:
            plan = stripe.Plan.create(
                product=instance.product.stripe_product_id,
                amount=instance.amount * 100,
                currency=instance.currency,
                interval=instance.interval,
                interval_count=instance.interval_count,
                trial_period_days=instance.trial_period_days,
            )
            instance.stripe_plan_id = plan.id
            instance.save()
        else:
            stripe.Plan.modify(
                instance.stripe_plan_id,
                # product=instance.product.stripe_product_id,
                trial_period_days=instance.trial_period_days,
            )
    except Exception as e:
        print(e)

# @receiver(post_delete, sender=Plan)
# def delete_stripe_plan(sender, instance, **kwargs):
#     try:
#         stripe.Plan.delete(instance.stripe_plan_id)
#     except Exception as e:
#         print(e)

@receiver(post_save, sender=Subscription)
def update_subscription_status(sender, instance, **kwargs):
    """Check and update subscription status after saving."""
    instance.check_and_update_status()

