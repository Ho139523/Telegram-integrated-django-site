from rest_framework import serializers
from .models import Cart, CartItem, Transaction, SplitPayment, Sale

class CartItemSerializer(serializers.ModelSerializer):
    unit_price = serializers.ReadOnlyField()
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = ['id', 'cart', 'product', 'variant', 'quantity', 'unit_price', 'total_price']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.ReadOnlyField()
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = Cart
        fields = ['id', 'profile', 'session_key', 'created_at', 'items', 'total_items', 'total_price']

class SplitPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SplitPayment
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    split_payments = SplitPaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_id', 'profile', 'cart', 'authority', 'amount',
            'status', 'zarinpal_ref_id', 'created_at', 'updated_at', 'split_payments'
        ]

class SaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sale
        fields = '__all__'
