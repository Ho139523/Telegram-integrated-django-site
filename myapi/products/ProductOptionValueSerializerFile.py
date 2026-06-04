from rest_framework import serializers
from products.models import ProductOptionValue
from myapi.products.ProductOptionSerializerFile import ProductOptionSerializer

class ProductOptionValueSerializer(serializers.ModelSerializer):
    option = ProductOptionSerializer()
    class Meta:
        model = ProductOptionValue
        fields = "__all__"