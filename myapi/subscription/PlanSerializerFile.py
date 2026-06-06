from rest_framework import serializers
from subscription.models import (
    Plan, Feature, PlanFeature,
    PlanPrice, Subscription,
    SubscriptionInvoice, Coupon
)
from myapi.subscription.PlanFeatureSerializerFile import PlanFeatureSerializer
from myapi.subscription.PlanPriceSerializerFile import PlanPriceSerializer


class PlanSerializer(serializers.ModelSerializer):
    features = PlanFeatureSerializer(many=True)
    prices = PlanPriceSerializer(many=True)

    class Meta:
        model = Plan
        fields = ["id", "code", "description", "features", "prices"]


