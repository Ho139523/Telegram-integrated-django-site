from rest_framework import serializers
from products.models import ProductOptionValue
from myapi.products.ProductOptionSerializerFile import ProductOptionSerializer


class ProductOptionValueSerializer(serializers.ModelSerializer):
    option_name = serializers.CharField(source="option.name", read_only=True)

    class Meta:
        model = ProductOptionValue
        fields = ["id", "option_name", "value"]


