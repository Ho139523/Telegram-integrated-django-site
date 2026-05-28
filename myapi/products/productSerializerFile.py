# serializers.py
from rest_framework import serializers
from products.models import Product, Category
from myapi.products.CategorySerializerFile import CategorySerializer
from myapi.products.ProductImagesSerializerFile import ProductImageSerializer
from AI.settings import SITE_DOMAIN

class ProductSerializer(serializers.ModelSerializer):
    code = serializers.CharField(read_only=True)
    category = CategorySerializer(read_only=True)
    images = serializers.SerializerMethodField()
    main_image = serializers.SerializerMethodField()


    class Meta:
        model = Product
        fields = ["id", "profile", "name", "slug", "brand", "price", "discount",
                  "stock", "status", "category", "description", "main_image", "images",
                  "code", "store", "unit", "min_quantity", "max_quantity", "quantity_step", "final_price"]
        
        read_only_fields = ["code"]  # code فقط خواندنی است
    
    def create(self, validated_data):
        # code را حذف نکنید! بگذارید مدل خودش تولید کند
        # فقط اگر کد در validated_data هست، حذفش کن (برای امنیت)
        validated_data.pop('code', None)
        return super().create(validated_data)
    
    def to_representation(self, instance):
        """اطمینان از نمایش code در خروجی"""
        data = super().to_representation(instance)
        # اگر code خالی بود، دوباره تلاش کن
        if not data.get('code') and instance.code:
            data['code'] = instance.code
        return data
    
    def get_main_image(self, obj):
        """برگرداندن URL کامل عکس اصلی با دامنه صحیح"""
        if obj.main_image:
            # استفاده از CURRENT_SITE که در settings.py تعریف شده
            from AI.settings import SITE_DOMAIN
            return f"{SITE_DOMAIN}{obj.main_image.url}"
        return None
    
    def get_images(self, obj):
        """برگرداندن URL کامل عکس‌های دیگر با دامنه صحیح"""
        from AI.settings import SITE_DOMAIN
        images_data = []
        for img in obj.images.all():
            images_data.append({
                'id': img.id,
                'image': f"{SITE_DOMAIN}{img.image.url}",
                'product': img.product.id
            })
        return images_data
    
