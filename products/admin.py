from django.contrib import admin
from .models import (
    TutorialModel, CategoryModel, ArticleModel,
    Category, Product, ProductAttribute, Store,
    ProductImage, ProductVariant, Unit
)


### ----------------------------
### 1. مدیریت دسته‌بندی‌ها
### ----------------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'parent', 'position', 'store')
    list_filter = ('status', 'store')
    search_fields = ('title', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['position']

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('parent', 'store')
        if hasattr(request.user, "profilemodel") and hasattr(request.user.profilemodel, "owned_store"):
            store = request.user.profilemodel.owned_store
            qs = qs.filter(store=store)
        return qs


### ----------------------------
### 2. مدیریت ویژگی‌ها و تصاویر
### ----------------------------
class ProductAttributeInline(admin.TabularInline):
    model = ProductAttribute
    extra = 1


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fk_name = 'product'  # ❌ قبلی parent بود، درست شد
    verbose_name = "Variant"
    verbose_name_plural = "Variants"


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'display_hierarchy', 'stock', 'final_price')
    search_fields = ('product__name', 'key', 'value', 'sku')
    list_filter = ('product',)

    def display_hierarchy(self, obj):
        names = [obj.value]
        parent = obj.parent
        while parent:
            names.append(parent.value)
            parent = parent.parent
        return " > ".join(reversed(names))
    display_hierarchy.short_description = "Variant Hierarchy"


### ----------------------------
### 3. مدیریت واحدهای اندازه‌گیری
### ----------------------------
@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("name", "symbol", "is_decimal", "store")
    list_filter = ("store",)
    search_fields = ("name", "symbol")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if hasattr(request.user, "profilemodel") and hasattr(request.user.profilemodel, "owned_store"):
            store = request.user.profilemodel.owned_store
            qs = qs.filter(store=store)
        return qs

    def save_model(self, request, obj, form, change):
        if not obj.store_id and hasattr(request.user.profilemodel, "owned_store"):
            obj.store = request.user.profilemodel.owned_store
        super().save_model(request, obj, form, change)


### ----------------------------
### 4. مدیریت محصولات
### ----------------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("code", 'name', 'price', "store", 'status', 'category', 'stock', 'unit')
    list_filter = ('status', "store", 'category',)
    search_fields = ('name', 'slug', 'category__title')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['-price', 'name']
    inlines = [ProductAttributeInline, ProductImageInline, ProductVariantInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('category', 'store', 'unit')
        if hasattr(request.user, "profilemodel") and hasattr(request.user.profilemodel, "owned_store"):
            qs = qs.filter(store=request.user.profilemodel.owned_store)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "unit" and hasattr(request.user, "profilemodel") and hasattr(request.user.profilemodel, "owned_store"):
            kwargs["queryset"] = Unit.objects.filter(store=request.user.profilemodel.owned_store)
        elif db_field.name == "category" and hasattr(request.user, "profilemodel") and hasattr(request.user.profilemodel, "owned_store"):
            kwargs["queryset"] = Category.objects.filter(store=request.user.profilemodel.owned_store)
        elif db_field.name == "store" and hasattr(request.user, "profilemodel") and hasattr(request.user.profilemodel, "owned_store"):
            kwargs["queryset"] = Store.objects.filter(id=request.user.profilemodel.owned_store.id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


### ----------------------------
### 5. مدیریت فروشگاه‌ها
### ----------------------------
@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'city', 'province')
    search_fields = ('name', 'owner__tel_id', 'city', 'province')


### ----------------------------
### 6. سایر مدل‌ها
### ----------------------------
@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ('product', 'key', 'value')
    list_filter = ('key',)
    search_fields = ('product__name', 'key', 'value')


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'image')


admin.site.register(TutorialModel)
admin.site.register(CategoryModel)
admin.site.register(ArticleModel)
