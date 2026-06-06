from rest_framework import serializers
from subscription.models import (
    Plan, Feature, PlanFeature,
    PlanPrice, Subscription, 
    SubscriptionInvoice, Coupon
    )


class PlanFeatureSerializer(serializers.ModelSerializer):
    feature_name = serializers.CharField(source="feature.name")

    class Meta:
        model = PlanFeature
        fields = ["feature_name", "value"]
