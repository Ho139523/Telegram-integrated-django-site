from rest_framework import serializer
from heartpred.models import heart


class HeartSerializer(serializer.ModelSerializer):
    class Meta:
        model = heart
        fields = "__all__"
