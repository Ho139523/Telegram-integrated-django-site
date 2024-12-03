from rest_framework import serializers
from .models import telbotid

class TelbotidSerializer(serializers.ModelSerializer):
    class Meta:
        model = telbotid
        fields = ['tel_id']