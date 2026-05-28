# utils/balebot/dynamic_serializers.py
from rest_framework import serializers
from django.db import models
from django.apps import apps
import inspect

class DynamicModelSerializer(serializers.ModelSerializer):
    """
    سریالایزر داینامیک که می‌تواند هر مدلی را سریالایز کند
    """
    class Meta:
        model = None
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        model = kwargs.pop('model', None)
        super().__init__(*args, **kwargs)
        if model:
            self.Meta.model = model

def get_serializer_for_model(model_class, depth=0):
    """
    ساخت سریالایزر برای هر مدل با قابلیت nested تا depth معین
    """
    from myapi.accounts.ProfileSerializerFile import ProfileSerializer, ProfileCheckSerializer
    
    # مدل‌های خاص با serializer سفارشی
    custom_serializers = {
        'ProfileModel': ProfileSerializer,
        'User': 'accounts.serializers.UserSerializer',  # مسیر به serializer
        'Store': 'products.serializers.StoreSerializer',
        'Product': 'products.serializers.ProductSerializer',
        'Category': 'products.serializers.CategorySerializer',
        'Address': 'accounts.serializers.AddressSerializer',
        'Transaction': 'payment.serializers.TransactionSerializer',
        'Cart': 'payment.serializers.CartSerializer',
    }
    
    class_name = model_class.__name__
    
    if class_name in custom_serializers:
        serializer_class = custom_serializers[class_name]
        if isinstance(serializer_class, str):
            # import dynamic
            module_path, class_name = serializer_class.rsplit('.', 1)
            module = __import__(module_path, fromlist=[class_name])
            serializer_class = getattr(module, class_name)
        return serializer_class
    
    # ساخت serializer داینامیک
    class AutoSerializer(serializers.ModelSerializer):
        class Meta:
            model = model_class
            fields = '__all__'
            read_only_fields = ['id', 'created_at', 'updated_at'] if hasattr(model_class, 'created_at') else ['id']
    
    return AutoSerializer