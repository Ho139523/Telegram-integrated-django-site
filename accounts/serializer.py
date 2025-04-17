from rest_framework import serializers
from .models import ProfileModel

class ProfileModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileModel
        fields = ['telegram']
