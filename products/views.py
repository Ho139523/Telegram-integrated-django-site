from rest_framework import viewsets, permissions
from accounts.models import ProfileModel
from .models import Store, Unit, Category, Product, ProductImage, ProductAttribute, ProductVariant, ProductOption, ProductOptionValue
from .serializers import (
    StoreSerializer, UnitSerializer, CategorySerializer, ProductSerializer,
    ProductImageSerializer, ProductAttributeSerializer, ProductVariantSerializer,
    ProductOptionSerializer, ProductOptionValueSerializer
)
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from utils.permissions import IsOwnerOrReadOnly, IsAdminOrReadOnly, BotSignaturePermission

class StoreViewSet(viewsets.ModelViewSet):
    serializer_class = StoreSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly, BotSignaturePermission]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Store.objects.all()
        try:
            profile = user.profilemodel
            return Store.objects.filter(owner=profile)
        except ProfileModel.DoesNotExist:
            return Store.objects.none()

    def perform_create(self, serializer):
        profile = self.request.user.profilemodel
        serializer.save(owner=profile)


class UnitViewSet(viewsets.ModelViewSet):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        # ادمین همه محصولات را ببیند
        if user.is_staff:
            return Product.objects.all()
        # فروشنده (Profile) فقط محصولات خودش
        try:
            profile = user.profilemodel
            return Product.objects.filter(profile=profile)
        except ProfileModel.DoesNotExist:
            # کاربران عادی هیچ محصولی ندارند
            return Product.objects.none()

    def perform_create(self, serializer):
        # محصول را به پروفایل صاحب متصل کن
        profile = self.request.user.profilemodel
        serializer.save(profile=profile, store=profile.get_default_store() or serializer.validated_data.get('store'))

class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class ProductAttributeViewSet(viewsets.ModelViewSet):
    queryset = ProductAttribute.objects.all()
    serializer_class = ProductAttributeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class ProductOptionViewSet(viewsets.ModelViewSet):
    queryset = ProductOption.objects.all()
    serializer_class = ProductOptionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class ProductOptionValueViewSet(viewsets.ModelViewSet):
    queryset = ProductOptionValue.objects.all()
    serializer_class = ProductOptionValueSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class ProductVariantViewSet(viewsets.ModelViewSet):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
