from rest_framework import serializers
from payment.models import Cart, CartItem
from myapi.accounts.ProfileSerializerFile import ProfileSerializer


class CartSerializer(serializers.ModelSerializer):
    # profile = ProfileSerializer()
    class Meta:
        model = Cart
        fields = ["id", "session_key", "created_at"]
        
