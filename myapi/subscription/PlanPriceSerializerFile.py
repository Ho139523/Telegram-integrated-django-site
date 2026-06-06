from rest_framework import serializers
from subscription.models import (
    Plan, Feature, PlanFeature,
    PlanPrice, Subscription,
    SubscriptionInvoice, Coupon
)


class PlanPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanPrice
        fields = ["months", "price"]
