from rest_framework import serializers
from products.models import ProductImage

class ProductImageSerializer(serializers.ModelSerializer):
    local_image = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = [
            "id",
            "image",
            "local_image",
            "product",
            "file_id",
        ]

    def get_local_image(self, obj):
        if obj.image:
            return obj.image.name
        return None    
