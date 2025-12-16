from rest_framework import serializers
from .models import (
    Store, Unit, Category, Product, ProductImage,
    ProductAttribute, ProductVariant, ProductOption, ProductOptionValue
)


from rest_framework import serializers
from .models import Store, Unit, Category, Product, ProductImage, ProductAttribute, ProductVariant, ProductOption, ProductOptionValue

class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = '__all__'

class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    parent_title = serializers.ReadOnlyField(source='parent.title')

    class Meta:
        model = Category
        fields = ['id', 'title', 'slug', 'status', 'parent', 'parent_title', 'position', 'store']

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'product']

class ProductAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductAttribute
        fields = ['id', 'key', 'value', 'product']

class ProductOptionValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductOptionValue
        fields = ['id', 'value', 'option']

class ProductOptionSerializer(serializers.ModelSerializer):
    values = ProductOptionValueSerializer(many=True, read_only=True)

    class Meta:
        model = ProductOption
        fields = ['id', 'name', 'product', 'values']

class ProductVariantSerializer(serializers.ModelSerializer):
    values = ProductOptionValueSerializer(many=True, read_only=True)
    final_price = serializers.ReadOnlyField()

    class Meta:
        model = ProductVariant
        fields = ['id', 'product', 'sku', 'price_override', 'stock', 'values', 'final_price']

class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    attributes = ProductAttributeSerializer(many=True, read_only=True)
    final_price = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            'id', 'profile', 'name', 'slug', 'brand', 'price', 'discount',
            'stock', 'status', 'category', 'description', 'main_image',
            'code', 'store', 'unit', 'min_quantity', 'max_quantity',
            'quantity_step', 'final_price', 'variants', 'images', 'attributes'
        ]

