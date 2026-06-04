from rest_framework import serializers
from products.models import ProductVariant
from myapi.products.productSerializerFile import ProductSerializer


class ProductVariantSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    class Meta:
        # values = 
        model = ProductVariant
        fields = ["id", "product","sku","price_override","stock","values"]