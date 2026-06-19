# serializers.py
from rest_framework import serializers
from products.models import Product, Category, ProductImage
from myapi.products.CategorySerializerFile import CategorySerializer
from myapi.products.ProductImagesSerializerFile import ProductImageSerializer
from AI.settings import SITE_DOMAIN

class ProductSerializer(serializers.ModelSerializer):
    code = serializers.CharField(read_only=True)
    category = CategorySerializer(read_only=True)

    images = serializers.SerializerMethodField()

    main_image = serializers.SerializerMethodField()
    main_image_local = serializers.SerializerMethodField()
    main_image_file_id = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "profile",
            "name",
            "slug",
            "brand",
            "price",
            "discount",
            "stock",
            "status",
            "category",
            "description",

            # main image (ALL MODES)
            "main_image",
            "main_image_local",
            "main_image_file_id",

            "images",

            "code",
            "store",
            "unit",
            "min_quantity",
            "max_quantity",
            "quantity_step",
            "final_price",
        ]

        read_only_fields = ["code"]

    # -------------------------
    # URL
    # -------------------------
    def get_main_image(self, obj):
        if obj.main_image:
            return f"{SITE_DOMAIN}{obj.main_image.url}"
        return None

    # -------------------------
    # LOCAL PATH
    # -------------------------
    def get_main_image_local(self, obj):
        if obj.main_image:
            return obj.main_image.name  # product_images/xxx.jpg
        return None

    # -------------------------
    # FILE_ID (🔥 مهم)
    # -------------------------
    def get_main_image_file_id(self, obj):
        return obj.main_image_file_id

    # -------------------------
    # IMAGES
    # -------------------------
    def get_images(self, obj):
        images_data = []

        for img in obj.images.all():
            images_data.append({
                "id": img.id,

                "file_id": img.file_id,

                "image": f"{SITE_DOMAIN}{img.image.url}",
                "local_image": img.image.name,

                "product": img.product.id,
            })

        return images_data

