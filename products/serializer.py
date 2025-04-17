from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    final_price = serializers.SerializerMethodField()

    def get_final_price(self, obj):
        if obj.discount > 0:
            discount_amount = (obj.price * obj.discount) / 100
            return obj.price - discount_amount
        return obj.price

    class Meta:
        model = Product
        fields = '__all__'

