from rest_framework import serializers
from .models import (
    Plan, Feature, PlanFeature,
    PlanPrice, Subscription,
    SubscriptionInvoice, Coupon
)


class PlanFeatureSerializer(serializers.ModelSerializer):
    feature_name = serializers.CharField(source="feature.name")

    class Meta:
        model = PlanFeature
        fields = ["feature_name", "value"]


class PlanPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanPrice
        fields = ["months", "price"]


class PlanSerializer(serializers.ModelSerializer):
    features = PlanFeatureSerializer(many=True)
    prices = PlanPriceSerializer(many=True)

    class Meta:
        model = Plan
        fields = ["id", "code", "description", "features", "prices"]


class SubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source="plan.get_code_display")
    days_left = serializers.SerializerMethodField()
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = [
            "plan_name",
            "status",
            "start_date",
            "end_date",
            "days_left",
            "is_valid",
        ]

    def get_days_left(self, obj):
        return obj.days_left()

    def get_is_valid(self, obj):
        return obj.is_valid
