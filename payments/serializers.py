# payments/serializers.py

from rest_framework import serializers
from payments.models.intent import PaymentIntent


class PaymentIntentSerializer(serializers.ModelSerializer):

    class Meta:
        model = PaymentIntent
        fields = [
            "id",
            "intent_id",
            "amount",
            "currency",
            "status",
        ]
