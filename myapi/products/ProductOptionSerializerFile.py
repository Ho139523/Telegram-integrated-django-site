from rest_framework import serializers
from products.models import ProductOption
from myapi.products.productSerializerFile import ProductSerializer


class ProductOptionSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    class Meta:
        model = ProductOption
        fields = "__all__"
