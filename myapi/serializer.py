from rest_framework import serializers
from heartpred.models import heart


class HeartSerializer(serializers.ModelSerializer):
    class Meta:
        model = heart
        fields = "__all__"
