from django.db import models, transaction
from decimal import Decimal
from accounts.models import User, ProfileModel
from django.core.exceptions import ValidationError
import os
import hashlib
from django.utils.text import slugify
import pycountry
from django.utils import timezone
from datetime import timedelta
from django.utils.text import slugify


# =========================
#  STORE MODEL
# =========================
class Store(models.Model):
    # ----------------------------
    # Language choices
    # ----------------------------
    def get_language_choices():
        languages = []
        for lang in pycountry.languages:
            if hasattr(lang, 'alpha_2'):
                languages.append((lang.alpha_2, lang.name))
        return sorted(languages, key=lambda x: x[1])

    owner = models.OneToOneField(
        ProfileModel, 
        on_delete=models.CASCADE, 
        related_name="owned_store", 
        verbose_name="Owner Profile"
    )
    name = models.CharField(max_length=100, unique=True, verbose_name='Store Name')
    logo = models.ImageField(upload_to="store_logos/", blank=True, null=True, verbose_name="Store Logo")
    tel_group = models.CharField(default="@", max_length=20, null=True, blank=True, verbose_name="Telegram group ID")
    tel_channel = models.CharField(default="@", max_length=20, unique=True, null=True, blank=True, verbose_name="Telegram channel ID")
    lang = models.CharField(max_length=10, choices=get_language_choices(), default='en', unique=False, null=False, blank=True)
    iban = models.CharField(
        max_length=26,
        blank=True,
        null=True,
        verbose_name="شماره شبا",
        help_text="شماره شبا باید با IR شروع شود."
    )
    tagline = models.CharField(max_length=120, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    banner_image = models.ImageField(upload_to="store_banners/", blank=True, null=True)
    intro_video = models.FileField(upload_to="store_intro_videos/", blank=True, null=True)  # یا URLField

    website = models.URLField(blank=True, null=True)
    support_phone = models.CharField(max_length=30, blank=True, null=True)
    support_email = models.EmailField(blank=True, null=True)

    is_verified = models.BooleanField(default=False)
    verification_level = models.CharField(max_length=20, default="basic")  # basic/verified/premium

    legal_name = models.CharField(max_length=200, blank=True, null=True)
    company_type = models.CharField(max_length=20, blank=True, null=True)  # individual/company
    tax_id = models.CharField(max_length=50, blank=True, null=True)

    min_order_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    lead_time_days = models.PositiveIntegerField(default=1)

    payment_terms = models.TextField(blank=True, null=True)
    return_policy = models.TextField(blank=True, null=True)

    # اگر دوست داری لینک‌ها را راحت نگه داری:
    social_links = models.JSONField(default=dict, blank=True)  # {"instagram":"...", "linkedin":"..."}

    
    status = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Store"
        verbose_name_plural = "Stores"


    
    def __str__(self):
        return self.name



    # متدهای کمکی برای آدرس
    def get_address(self):
        """آدرس فروشگاه را برمی‌گرداند (از مدل Address)"""
        if hasattr(self, 'store_address'):
            return self.store_address
        return None

    def set_address(self, address_data):
        """تنظیم آدرس برای فروشگاه"""
        from django.core.exceptions import ValidationError
        
        # حذف آدرس قبلی اگر وجود داشته باشد
        if hasattr(self, 'store_address'):
            self.store_address.delete()
        
        # ایجاد آدرس جدید
        try:
            address = Address.objects.create(
                store=self,
                **address_data
            )
            return address
        except Exception as e:
            raise ValidationError(f"خطا در ایجاد آدرس: {str(e)}")

    @property
    def full_address(self):
        """آدرس کامل فروشگاه را به صورت متنی برمی‌گرداند"""
        addr = self.get_address()
        if addr:
            parts = []
            if addr.shipping_line1:
                parts.append(addr.shipping_line1)
            if addr.shipping_line2:
                parts.append(addr.shipping_line2)
            if addr.shipping_city:
                parts.append(addr.shipping_city)
            if addr.shipping_province:
                parts.append(addr.shipping_province)
            if addr.shipping_country:
                parts.append(addr.shipping_country)
            if addr.shipping_zip_code:
                parts.append(f"کد پستی: {addr.shipping_zip_code}")
            
            return "، ".join(parts)
        # Fallback به فیلدهای قدیمی
        parts = []
        if self.address:
            parts.append(self.address)
        if self.city:
            parts.append(self.city)
        if self.province:
            parts.append(self.province)
        
        if self.owner.lang == "fa":
            return "، ".join(parts) if parts else t('message', 'address_not_set', chat_id=self.owner.tel_id)
        else:
            return ", ".join(parts) if parts else t('message', 'address_not_set', chat_id=self.owner.tel_id)



    @property
    def short_address(self):
        addr = self.get_address()
        if addr:
            parts = []
            if addr.shipping_country:
                parts.append(addr.shipping_country_name)
            if addr.shipping_province:
                parts.append(addr.shipping_province_name)
            if addr.shipping_city:
                parts.append(addr.shipping_city_name)
        if self.owner.lang == "fa":
            return "، ".join(parts) if parts else t('message', 'address_not_set', chat_id=self.owner.tel_id)
        else:
            return ", ".join(parts) if parts else t('message', 'address_not_set', chat_id=self.owner.tel_id)




# =========================
#  UNIT MODEL (Per Store)
# =========================

class UnitManager(models.Manager):  # ✅ اضافه شد
    def for_store(self, store):
        """برگرداندن فقط واحدهای یک فروشگاه خاص"""
        return self.filter(store=store)


class Unit(models.Model):
    store = models.ForeignKey('Store', on_delete=models.CASCADE, related_name="units", verbose_name="Store")
    name = models.CharField(max_length=50, verbose_name="Unit Name")
    symbol = models.CharField(max_length=10, verbose_name="Symbol")
    is_decimal = models.BooleanField(default=False, help_text="آیا واحد می‌تواند اعشاری باشد؟")

    objects = UnitManager()  # ✅ اضافه شد

    class Meta:
        unique_together = ('store', 'name')  # ✅ هر فروشگاه نمی‌تواند دو واحد همنام داشته باشد
        verbose_name = "Unit"
        verbose_name_plural = "Units"

    def __str__(self):
        return f"{self.name} ({self.symbol})"


# =========================
#  CATEGORY (Hierarchical)
# =========================

class Category(models.Model):
    title = models.CharField(max_length=50, unique=False, verbose_name='Category Title')
    slug = models.SlugField(unique=True, verbose_name='Slug')
    status = models.BooleanField(default=True, verbose_name='Publish Status')
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True,
        related_name='subcategories', verbose_name='Parent Category'
    )
    position = models.IntegerField(default=1, verbose_name='Position')
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='categories', verbose_name='Store')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["position"]

    def get_parents(self):
        parents = []
        category = self
        while category.parent:
            parents.append(category.parent)
            category = category.parent
        return parents

    def get_full_path(self):
        return " / ".join([p.title for p in reversed(self.get_parents())] + [self.title])

    def get_all_subcategories(self):
        subcategories = set()
        categories_to_check = [self]
        while categories_to_check:
            current = categories_to_check.pop()
            children = current.subcategories.all()
            subcategories.update(children)
            categories_to_check.extend(children)
        return subcategories

    def get_next_layer_categories(self, status=True, both=False):
        if both:
            return self.subcategories.filter()
        return self.subcategories.filter(status=status)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "status": self.status,
            "parent": self.parent.title if self.parent else None,
            "position": self.position,
            "store": self.store.name if self.store else None,
        }


    def _generate_unique_slug(self):
        base_slug = slugify(self.slug or self.title)
        slug = base_slug
        counter = 1

        while Category.objects.exclude(pk=self.pk).filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug

    

    def save(self, *args, **kwargs):
        self.slug = self._generate_unique_slug()

        # self.full_clean()   # <-- اعتبارسنجی

        is_new = self.pk is None

        super().save(*args, **kwargs)

        if is_new and self.parent:
            if self.parent.products.exists():
                with transaction.atomic():
                    self.parent.products.update(category=self)


# =========================
#  PRODUCT MODEL
# =========================

class Product(models.Model):
    profile = models.ForeignKey(ProfileModel, on_delete=models.CASCADE, related_name="profilemodel")
    name = models.CharField(max_length=100, verbose_name='Product Name')
    slug = models.SlugField(unique=True, verbose_name='Slug')
    brand = models.CharField(max_length=50, blank=True, null=True, verbose_name='Brand')
    price = models.DecimalField(max_digits=20, decimal_places=2, verbose_name='Price')
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Discount (%)')
    stock = models.PositiveIntegerField(default=0, verbose_name='Stock')
    status = models.BooleanField(default=True, verbose_name='Status')
    category = models.ForeignKey('Category', on_delete=models.CASCADE, null=True, related_name='products', verbose_name='Category')
    description = models.TextField(blank=True, null=True, verbose_name='Description')
    main_image = models.ImageField(upload_to='product_images/', blank=True, null=True, verbose_name='Main Image')
    main_image_file_id = models.CharField(max_length=255, null=True, blank=True, db_index=True, verbose_name="Main Image File ID")
    code = models.CharField(max_length=10, unique=True, editable=False, blank=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='product_store', verbose_name='Store')
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Unit of Measure")
    min_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Minimum Quantity")
    max_quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Maximum Quantity")
    quantity_step = models.DecimalField(max_digits=10, decimal_places=2, default=1, verbose_name="Quantity Step")

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
    
    @property
    def final_price(self):
        """
        قیمت نهایی محصول بعد از اعمال تخفیف (بدون Variant)
        """
        price = Decimal(str(self.price))

        if self.discount:
            discount = Decimal(str(self.discount)) / Decimal("100")
            return price * (Decimal("1") - discount)

        return price





    def has_variants(self):
        """
        بررسی می‌کند که آیا محصول واقعاً واریانت فعال دارد
        """
        if not self.pk:
            return False
        
        # بررسی مستقیم از دیتابیس (بدون کش)
        from .models import ProductVariant  # import در داخل تابع برای جلوگیری از circular import
        return ProductVariant.objects.filter(product=self).exists()

    def get_active_variants_count(self):
        """تعداد واریانت‌های فعال را برمی‌گرداند"""
        if not self.pk:
            return 0
        from .models import ProductVariant
        return ProductVariant.objects.filter(product=self).count()

    def sync_stock(self):
        # اگر هنوز ذخیره نشده، کاری نکن
        if not self.pk:
            return

        if self.has_variants():
            total_stock = (
                self.variants.aggregate(total=models.Sum("stock"))["total"] or 0
            )
            self.stock = total_stock

    def _manual_stock_change(self):
        if not hasattr(self, "_old_stock"):
            self._old_stock = Product.objects.only("stock").get(pk=self.pk).stock
        return self.stock != self._old_stock 

    def clean(self):
        if self.category and self.category.get_next_layer_categories().exists():
            raise ValidationError({'category': "This category includes subcategories."})

        if self.price < 10000:
            raise ValidationError({'price': 'قیمت نمی‌تواند کمتر از 10000 باشد.'})

        system_update = getattr(self, "_system_stock_update", False)
        
        if (
            self.pk
            and self.has_variants()
            and not system_update
            and self._manual_stock_change()
        ):
            raise ValidationError({
                "stock": "موجودی محصول دارای واریانت به‌صورت خودکار محاسبه می‌شود."
            })

    def save(self, *args, **kwargs):
        # گرفتن system_update از kwargs یا attribute
        system_update = kwargs.pop('system_update', getattr(self, "_system_stock_update", False))
        
        # ست کردن system_update روی آبجکت
        self._system_stock_update = system_update

        # validation
        self.full_clean(exclude=["stock"] if system_update else [])

        # تولید کد محصول
        if not self.code:
            counter, _ = ProductCodeCounter.objects.get_or_create(id=1)
            self.code = counter.get_next_code()

        is_creating = self.pk is None

        super().save(*args, **kwargs)

        # فقط بعد از اینکه PK گرفت
        if not is_creating and system_update:
            self.sync_stock()
            super().save(update_fields=["stock"])   


# =========================
#  OTHER MODELS
# =========================

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/', verbose_name='Product Image')
    file_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True
    )

    def __str__(self):
        return f"{self.product.name} - Image {self.id}"


class ProductAttribute(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='attributes')
    key = models.CharField(max_length=50, verbose_name='Attribute Key')
    value = models.CharField(max_length=100, verbose_name='Attribute Value')

    def __str__(self):
        return f"{self.key}: {self.value}"


class ProductCodeCounter(models.Model):
    counter = models.BigIntegerField(default=1, unique=True)

    def get_next_code(self):
        self.counter += 1
        self.save()
        return f"{self.counter:010d}"

    def reset_counter(self, start_value=1):
        self.counter = start_value
        self.save()


import hashlib
from django.db import models
from django.utils.text import slugify

# =========================
# VARIANT SYSTEM (PROFESSIONAL STRUCTURE)
# =========================

class ProductOption(models.Model):
    """نوع ویژگی (مثلاً رنگ، سایز، جنس)"""
    product = models.ForeignKey("Product", on_delete=models.CASCADE, related_name="options")
    name = models.CharField(max_length=100, verbose_name="Option Name")  # مثل "رنگ" یا "سایز"

    class Meta:
        unique_together = ("product", "name")
        verbose_name = "Product Option"
        verbose_name_plural = "Product Options"

    def __str__(self):
        return f"{self.product.name} - {self.name}"


class ProductOptionValue(models.Model):
    """مقدار ویژگی (مثلاً قرمز، آبی، XL)"""
    option = models.ForeignKey("ProductOption", on_delete=models.CASCADE, related_name="values")
    value = models.CharField(max_length=100, verbose_name="Option Value")

    class Meta:
        unique_together = ("option", "value")
        verbose_name = "Product Option Value"
        verbose_name_plural = "Product Option Values"

    def __str__(self):
        return f"{self.option.name}: {self.value}"


class ProductVariant(models.Model):
    product = models.ForeignKey("Product", on_delete=models.CASCADE, related_name="variants")
    sku = models.CharField(max_length=150, unique=True, blank=True, null=True, verbose_name="SKU Code")
    price_override = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True, verbose_name="Custom Price")
    stock = models.PositiveIntegerField(default=0, verbose_name="Stock Quantity")
    values = models.ManyToManyField("ProductOptionValue", related_name="variants", blank=True)

    class Meta:
        verbose_name = "Product Variant"
        verbose_name_plural = "Product Variants"
        indexes = [
            models.Index(fields=["product"]),
            models.Index(fields=["sku"]),
        ]

    def __str__(self):
        values_str = " / ".join([v.value for v in self.values.all()])
        return f"{self.product.name} ({values_str})" if values_str else self.product.name

    @property
    def final_price(self):
        return self.price_override if self.price_override else self.product.final_price

    

    def generate_sku(self):
        """
        تولید SKU بر اساس ترکیب مقادیر فعلی.
        این تابع فرض می‌کند که مقادیر (values) قبلاً ست شده‌اند.
        """
        value_names = [slugify(v.option.name + "-" + v.value).upper() for v in self.values.all()]
        parts = [f"P{self.product.id}"] + value_names
        base_sku = "-".join(parts) if parts else f"P{self.product.id}"
        hash_suffix = hashlib.md5(base_sku.encode()).hexdigest()[:6].upper()
        return f"{base_sku}-{hash_suffix}"

    def ensure_sku(self, save_if_missing=True):
        """
        اگر SKU خالی است و values موجود است، SKU را تولید و ذخیره کن.
        این متد را بعد از اضافه شدن m2m یا در کد view صدا بزنید.
        """
        if not self.sku and self.values.exists():
            # تلاش برای تولید SKU منحصر‌به‌فرد
            base = self.generate_sku()
            final_sku = f"{base}"
            counter = 1
            # loop برای جلوگیری از collision احتمالی
            while ProductVariant.objects.filter(sku=final_sku).exclude(pk=self.pk).exists():
                final_sku = f"{base}-{counter}"
                counter += 1
            self.sku = final_sku
            if save_if_missing:
                self.save(update_fields=["sku"])



    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
    
            product = self.product
            product._system_stock_update = True  # 🔴 خیلی مهم
            product.sync_stock()
            product.save(update_fields=["stock"])
    
    
    
    
    

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            product = self.product
            super().delete(*args, **kwargs)

            product.sync_stock()
            product.save(update_fields=["stock"])

