from django.contrib import admin
from django.utils.html import format_html
from django.core.exceptions import ValidationError
from django.forms import ModelForm, BooleanField
from .models import Product, Plan, PlanType, Payment, Subscription

class ProductAdminForm(ModelForm):
    # create_billing_plans = BooleanField(initial=False, required=False, label="Créer des plans de facturation mensuel et annuel")

    class Meta:
        model = Product
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        product_type = cleaned_data.get("type")
        if product_type == PlanType.FREE.value[0]:
            if Product.objects.filter(type=PlanType.FREE.value[0]).exclude(id=self.instance.id).exists():
                raise ValidationError("Vous ne pouvez pas créer plusieurs produits gratuits.")
        return cleaned_data

class PlanInline(admin.TabularInline):
    model = Plan
    extra = 2

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['interval_count', 'interval', 'amount', 'currency']
        else:
            return []

class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    inlines = [PlanInline]
    list_display = ("name", "description", "storage", "type", "active", "created_at")
    list_editable = ["active"]
    search_fields = ["name", "description"]
    search_help_text = "Rechercher un produit via son nom ou sa description"
    list_filter = ["type", "active"]
    save_on_top = True

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # if not change and form.cleaned_data.get('create_billing_plans'):
        #     Plan.objects.create(
        #         product=obj,
        #         active=True,
        #         amount=1000,  # Example amount for monthly plan
        #         interval='month',
        #         interval_count=1,
        #         trial_period_days=30,
        #     )
        #     Plan.objects.create(
        #         product=obj,
        #         active=True,
        #         amount=10000,  # Example amount for yearly plan
        #         currency='EUR',
        #         interval='year',
        #         interval_count=1,
        #         trial_period_days=30,
        #     )

class PlanAdmin(admin.ModelAdmin):
    list_display = ("product", "amount", "currency", "interval", 'interval_count', 'trial_period_days', "active", "created_at")
    list_editable = ["active"]
    search_fields = ["product__name"]
    search_help_text = "Rechercher un plan via le nom du produit"
    list_filter = ["active", 'product', "interval"]
    save_on_top = True
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['interval_count', "product", 'interval', 'amount', 'currency']
        else:
            return []

class PaymentAdmin(admin.ModelAdmin):
    list_display = ("subscription", "subscription__plan", "subscription__user", "amount", "currency", "paid", "created_at", "updated_at")
    search_fields = ["user__username", "plan__product__name"]
    list_filter = ["status", "subscription__user", "subscription__plan", "subscription"]
    readonly_fields = ["subscription", "stripe_payment_intent_id", "amount", "currency", "status", "billing_reason", "created", "customer_email", "hosted_invoice_url", "invoice_pdf", "stripe_invoice_id", "paid", "period_end", "period_start", "amount_due", "amount_paid", "created_at", "updated_at"]

class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "status", "created_at", "updated_at")
    search_fields = ["user__username", "plan__product__name"]
    list_filter = ["status", "user", "plan"]
    # readonly_fields = ["user", "plan", "stripe_subscription_id", "stripe_session_id", "current_period_start", "current_period_end"]

admin.site.register(Product, ProductAdmin)
admin.site.register(Plan, PlanAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Subscription, SubscriptionAdmin)