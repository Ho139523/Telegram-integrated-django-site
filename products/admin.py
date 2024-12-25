from django.contrib import admin
from .models import TutorialModel, CategoryModel, ArticleModel#, ShoeModel
from .models import Category, Product, ProductAttribute, Store, ProductImage


### **1. مدیریت دسته‌بندی‌ها**
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'parent', 'position')  # ستون‌هایی که نمایش داده می‌شوند
    list_filter = ('status',)  # فیلتر براساس وضعیت انتشار
    search_fields = ('title', 'slug')  # جستجو براساس نام و اسلاگ
    prepopulated_fields = {'slug': ('title',)}  # تولید خودکار slug از عنوان
    ordering = ['position']  # ترتیب نمایش

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent')  # بهینه‌سازی Query برای parent


### **2. مدیریت محصولات**
class ProductAttributeInline(admin.TabularInline):
    model = ProductAttribute
    extra = 1  # تعداد خطوط خالی برای افزودن ویژگی جدید


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1  # تعداد خطوط خالی برای افزودن تصویر جدید


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_available', 'category', 'stock')  # ستون‌های نمایش داده شده
    list_filter = ('is_available', 'category',)  # فیلتر براساس وضعیت و دسته‌بندی
    search_fields = ('name', 'slug', 'category__title')  # جستجو براساس نام، اسلاگ و دسته‌بندی
    prepopulated_fields = {'slug': ('name',)}  # تولید خودکار slug از نام
    ordering = ['-price', 'name']  # ترتیب پیش‌فرض
    inlines = [ProductAttributeInline]  # ویژگی‌ها و تصاویر در صفحه محصول

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category')  # بهینه‌سازی Query برای دسته‌بندی


### **3. مدیریت فروشگاه‌ها**
@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'city', 'province')  # ستون‌های نمایش داده شده
    search_fields = ('name', 'user__username', 'city', 'province')  # جستجو براساس نام فروشگاه، کاربر، شهر و استان
    filter_horizontal = ('products',)  # افزودن قابلیت فیلتر برای محصولات مرتبط


### **4. مدیریت ویژگی‌های محصول (در صورت نیاز جداگانه)**
@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ('product', 'key', 'value')  # ستون‌های نمایش داده شده
    list_filter = ('key',)  # فیلتر براساس نام ویژگی
    search_fields = ('product__name', 'key', 'value')  # جستجو براساس نام محصول و ویژگی


### **5. مدیریت تصاویر محصول (در صورت نیاز جداگانه)**
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'image')  # نمایش شناسه و تصویر

admin.site.register(TutorialModel)
admin.site.register(CategoryModel)
admin.site.register(ArticleModel)
#admin.site.register(ShoeModel)
