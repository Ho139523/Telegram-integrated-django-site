from rest_framework import serializers
from .models import ShoeModel

class ShoeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoeModel
        fields = "__all__"