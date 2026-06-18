from os import O_WRONLY
import traceback
from rest_framework import viewsets
from cv import views
from myapi import serializer
from myapi.products.CodeSerializerFile import CodeSerializer
from products.models import ProductOption, Store, Product, ProductCodeCounter
from myapi.products.StoreSerializerFile import *
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
import traceback
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from myapi.products.productSerializerFile import ProductSerializer
from rest_framework.permissions import AllowAny

from products.serializers import ProductOptionSerializer
from products.serializers import ProductOptionValueSerializer
from products.models import ProductOption, ProductOptionValue


class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer

    @action(detail=True, methods=["GET"], url_path="profile")
    def profile_stores(self, request):
        bale_id = request.query_params.get('bale_id')
        name = request.query_params.get('name')
        
        if not bale_id or not name:
            return Response({"error": "bale_id and name are required"}, status=400)
        
        try:
            store = Store.objects.get(owner__bale_id=bale_id, name=name)
            serializer = self.get_serializer(store)
            return Response(serializer.data)
        except Store.DoesNotExist:
            return Response({"error": "Store not found"}, status=404)
        



class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    throttle_classes = []
    
    def get_object(self):
        """
        پشتیبانی از id و code (حفظ صفرها)
        """
        queryset = self.get_queryset()
        lookup_value = self.kwargs.get('pk')
        
        if not lookup_value:
            raise NotFound("Product not found")
        
        lookup_str = str(lookup_value)
        
        # اگر طول رشته 10 رقم است و فقط عدد دارد → احتمالاً code است
        if len(lookup_str) == 10 and lookup_str.isdigit():
            try:
                return queryset.get(code=lookup_str)
            except Product.DoesNotExist:
                pass
        
        # اگر عدد است → id
        if lookup_str.isdigit():
            try:
                return queryset.get(code=int(lookup_str))
            except Product.DoesNotExist:
                pass
        
        raise NotFound("Product not found")

    @action(detail=False, methods=["POST"], url_path="variants", permission_classes=[AllowAny])
    def _get_product_variants(self, request):
        code = request.data.get("product_code")
        
        try:
            product = Product.objects.get(code=code)
            
            # ✅ بهینه شده با prefetch_related
            variants = product.variants.all().prefetch_related(
                'values__option'  # پیش‌بارگذاری values و option آنها
            )
            
            serializer = ProductVariantSerializer(variants, many=True)
            return Response(serializer.data)
            
        except Product.DoesNotExist:
            return Response(
                {"error": "Product not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    


from myapi.products.ProductVariantSerializerFile import ProductVariantSerializer
from products.models import ProductVariant

    
class ProductVariantViewSet(viewsets.ModelViewSet):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantSerializer
    permission_classes = [AllowAny]
    throttle_classes = []



class ProductOptionViewSet(viewsets.ModelViewSet):
    queryset = ProductOption.objects.all()
    serializer_class = ProductOptionSerializer

class ProductOptionValueViewSet(viewsets.ModelViewSet):
    queryset = ProductOptionValue.objects.all()
    serializer_class = ProductOptionValueSerializer


