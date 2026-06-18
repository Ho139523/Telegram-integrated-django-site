from rest_framework import serializers
from payment.models import CartItem
from myapi.products.productSerializerFile import ProductSerializer
from myapi.products.ProductVariantSerializerFile import ProductVariantSerializer


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    variant = ProductVariantSerializer()

    class Meta:
        model = CartItem
        fields = "__all__"
