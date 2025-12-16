from django.db import models, transaction
from accounts.models import User, ProfileModel
from django.core.exceptions import ValidationError
import os
import hashlib
from django.utils.text import slugify





# =========================
#  STORE MODEL
# =========================

class Store(models.Model):
    owner = models.OneToOneField(ProfileModel, on_delete=models.CASCADE, related_name="owned_store", verbose_name="Owner Profile")
    name = models.CharField(max_length=100, verbose_name='Store Name')
    address = models.CharField(max_length=255, verbose_name='Address')
    city = models.CharField(max_length=50, verbose_name='City')
    province = models.CharField(max_length=50, verbose_name='Province')
    logo = models.ImageField(upload_to="store_logos/", blank=True, null=True, verbose_name="Store Logo")
    tel_group = models.CharField(default="@", max_length=20, null=True, blank=True, verbose_name="Telegram group ID")
    tel_channel = models.CharField(default="@", max_length=20, null=True, blank=True, verbose_name="Telegram channel ID")

    markant_id = models.CharField(max_length=36, verbose_name="Markant ID", unique=True, null=False, blank=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Store"
        verbose_name_plural = "Stores"


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
    title = models.CharField(max_length=50, unique=True, verbose_name='Category Title')
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
        return " > ".join([p.title for p in reversed(self.get_parents())] + [self.title])

    def get_all_subcategories(self):
        subcategories = set()
        categories_to_check = [self]
        while categories_to_check:
            current = categories_to_check.pop()
            children = current.subcategories.all()
            subcategories.update(children)
            categories_to_check.extend(children)
        return subcategories

    def get_next_layer_categories(self):
        return self.subcategories.filter(status=True)

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

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and self.parent:
            parent_category = self.parent
            if parent_category.products.exists():
                with transaction.atomic():
                    parent_category.products.update(category=self)
            self.save(update_fields=["parent"])


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
        if self.discount:
            return float(self.price) * (1 - float(self.discount)/100)
        return float(self.price)


    def has_variants(self):
        return self.variants.exists()

    def sync_stock(self):
        if self.has_variants():
            self.stock = (
                self.variants.aggregate(total=models.Sum("stock"))["total"] or 0
            )
            self._system_stock_update = True


    def _manual_stock_change(self):
        if not hasattr(self, "_old_stock"):
            self._old_stock = Product.objects.only("stock").get(pk=self.pk).stock
        return self.stock != self._old_stock 


    def clean(self):
        if self.category and self.category.get_next_layer_categories().exists():
            raise ValidationError({'category': "This category includes subcategories."})

        if self.price < 10000:
            raise ValidationError({'price': 'قیمت نمی‌تواند کمتر از 10000 باشد.'})

        if (
            self.pk
            and self.has_variants()
            and not getattr(self, "_system_stock_update", False)
            and self._manual_stock_change()
        ):
            raise ValidationError({
                "stock": "موجودی محصول دارای واریانت به‌صورت خودکار محاسبه می‌شود."
            })


    def save(self, *args, **kwargs):
        self.full_clean(exclude=["stock"])

        if not self.code:
            counter, _ = ProductCodeCounter.objects.get_or_create(id=1)
            self.code = counter.get_next_code()

        self.sync_stock()
        super().save(*args, **kwargs)

        # پاک‌کردن فلگ سیستمی
        if hasattr(self, "_system_stock_update"):
            del self._system_stock_update


# =========================
#  OTHER MODELS
# =========================

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/', verbose_name='Product Image')

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
            product.sync_stock()
            product.save(update_fields=["stock"])

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            product = self.product
            super().delete(*args, **kwargs)

            product.sync_stock()
            product.save(update_fields=["stock"])

