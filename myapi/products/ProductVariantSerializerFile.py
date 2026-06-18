from rest_framework import serializers
from products.models import ProductVariant
from myapi.products.productSerializerFile import ProductSerializer
from myapi.products.ProductOptionValueSerializerFile import ProductOptionValueSerializer


class ProductVariantSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    values = ProductOptionValueSerializer(many=True, read_only=True)
    class Meta:
        # values = 
        model = ProductVariant
        fields = ["id", "product","sku","price_override","stock","values"]
