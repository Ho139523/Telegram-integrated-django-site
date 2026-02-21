from django.contrib import admin
from django.utils import timezone
from .models import (
    Plan, Feature, PlanFeature, PlanPrice, 
    Coupon, Subscription, SubscriptionInvoice, Payment, SubscriptionUsage
)

# =============================
# Plan & Features
# =============================
@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ["code", "description", "is_active", "order"]
    list_editable = ["is_active", "order"]
    search_fields = ["code", "description"]
    ordering = ["order"]

@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "description"]
    search_fields = ["code", "name"]

@admin.register(PlanFeature)
class PlanFeatureAdmin(admin.ModelAdmin):
    list_display = ["plan", "feature", "value"]
    list_filter = ["plan"]
    search_fields = ["feature__name", "plan__code"]

@admin.register(PlanPrice)
class PlanPriceAdmin(admin.ModelAdmin):
    list_display = ["plan", "months", "price", "is_active"]
    list_filter = ["plan", "months", "is_active"]
    search_fields = ["plan__code"]
    ordering = ["plan", "months"]

# =============================
# Coupon
# =============================
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ["code", "discount_type", "value", "max_usage", "used_count", "valid_from", "valid_until", "is_active"]
    list_filter = ["discount_type", "is_active"]
    search_fields = ["code"]
    date_hierarchy = "valid_until"

# =============================
# Subscription Admin
# =============================
class SubscriptionUsageInline(admin.TabularInline):
    model = SubscriptionUsage
    extra = 0
    readonly_fields = ["feature", "used_count"]
    can_delete = False

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("store", "plan", "status", "start_date", "end_date", "days_left", "is_auto_renew")
    list_filter = ("status", "plan", "is_auto_renew")
    search_fields = ("store__name", "store__owner__user__username", "store__owner__user__email")
    date_hierarchy = "end_date"
    readonly_fields = ("start_date",)
    inlines = [SubscriptionUsageInline]
    actions = ["expire_selected", "activate_selected", "reset_usage_selected"]

    def expire_selected(self, request, queryset):
        for sub in queryset:
            sub.status = "expired"
            sub.save(update_fields=["status"])
        self.message_user(request, "✅ اشتراک های انتخاب شده منقضی شدند.")
    expire_selected.short_description = "Expire selected subscriptions"

    def activate_selected(self, request, queryset):
        for sub in queryset:
            sub.status = "active"
            sub.save(update_fields=["status"])
        self.message_user(request, "✅ اشتراک های انتخاب شده فعال شدند.")
    activate_selected.short_description = "Activate selected subscriptions"

    def reset_usage_selected(self, request, queryset):
        for sub in queryset:
            for usage in sub.usages.all():
                usage.used_count = 0
                usage.save(update_fields=["used_count"])
        self.message_user(request, "✅ Usage تمام سابسکریپشن های انتخاب شده ریست شد.")
    reset_usage_selected.short_description = "Reset usage for selected subscriptions"

# =============================
# SubscriptionInvoice + Payment Inline
# =============================
class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ["amount", "status", "authority", "ref_id", "created_at", "card_pan", "card_hash"]
    can_delete = False

@admin.register(SubscriptionInvoice)
class SubscriptionInvoiceAdmin(admin.ModelAdmin):
    list_display = ("subscription", "plan_price", "amount", "coupon", "is_paid", "created_at")
    list_filter = ("is_paid", "created_at")
    search_fields = ("subscription__store__name", "plan_price__plan__code")
    date_hierarchy = "created_at"
    inlines = [PaymentInline]

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("invoice", "amount", "status", "authority", "ref_id", "created_at", "card_pan")
    list_filter = ("status",)
    search_fields = ("authority", "ref_id")
    readonly_fields = ("created_at", "card_pan", "card_hash")
