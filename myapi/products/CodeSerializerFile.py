from rest_framework import serializers
from products.models import ProductCodeCounter

class CodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCodeCounter
        fields = "__all__"