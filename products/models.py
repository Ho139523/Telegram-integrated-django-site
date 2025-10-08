from django.db import models, transaction
from accounts.models import User, ProfileModel
from django.core.exceptions import ValidationError
import os


# =========================
#  CATEGORY MODEL
# =========================

class CategoryModel(models.Model):
    title = models.CharField(max_length=50, unique=True, verbose_name='Title')
    slug = models.SlugField(unique=True)
    status = models.BooleanField(default=True, verbose_name='Publish Status')
    position = models.IntegerField(verbose_name='Position')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["position"]


# =========================
#  TUTORIAL MODEL
# =========================

class TutorialModel(models.Model):
    title = models.CharField(max_length=50, unique=True, verbose_name='Title')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Price')
    video = models.FileField(upload_to='tutorial_videos/', verbose_name='Video')
    video_poster = models.ImageField(upload_to='tutorial_posters/', verbose_name='Video Poster')
    poster = models.ImageField(upload_to='tutorial_poster/', verbose_name='Tutorial Poster')
    about = models.TextField(max_length=5000, verbose_name='Description')
    tag = models.ForeignKey(CategoryModel, on_delete=models.SET_NULL, null=True, verbose_name='Tag')
    status = models.BooleanField(default=False, verbose_name='Publish Status')
    slug = models.SlugField(unique=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='tutorials_authored', verbose_name='Author')
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='tutorials_taught', verbose_name='Teacher')
    attachment = models.FileField(upload_to='tutorial_attachments/', blank=True, null=True, verbose_name='Attachments')
    created = models.DateTimeField(auto_now_add=True, verbose_name="Date of creation")
    installment = models.BooleanField(default=False, verbose_name='Installment Purchase')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Tutorial"
        verbose_name_plural = "Tutorials"
        ordering = ["created"]


# =========================
#  ARTICLE MODEL
# =========================

class ArticleModel(models.Model):
    title = models.CharField(max_length=50, unique=True, verbose_name='Title')
    poster = models.ImageField(upload_to='article_poster/', verbose_name='Article Poster')
    context = models.TextField(max_length=5000, verbose_name='Description')
    tag = models.ForeignKey(CategoryModel, on_delete=models.SET_NULL, null=True, verbose_name='Tag')
    status = models.BooleanField(default=False, verbose_name='Publish Status')
    slug = models.SlugField(unique=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='article_authored', verbose_name='Author')
    attachment = models.FileField(upload_to='tutorial_attachments/', blank=True, null=True, verbose_name='Attachments')
    created = models.DateTimeField(auto_now_add=True, verbose_name="Date of creation")
    time_takes = models.IntegerField(verbose_name='Time it takes to read it')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        ordering = ["created"]

    @property
    def required_time(self):
        hour = self.time_takes // 60
        minute = self.time_takes % 60
        return [hour, minute]


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

    @property
    def final_price(self):
        if self.discount > 0:
            discount_amount = (self.price * self.discount) / 100
            return self.price - discount_amount
        return self.price

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def clean(self):
        if self.category and self.category.get_next_layer_categories().exists():
            raise ValidationError({'category': "This category includes subcategories. You can't add product to it."})
        if self.price < 10000:
            raise ValidationError({'price': 'قیمت نمی‌تواند کمتر از 10000 باشد.'})

    def save(self, *args, **kwargs):
        self.clean()
        if not self.code:
            product_code_counter, _ = ProductCodeCounter.objects.get_or_create(id=1)
            self.code = product_code_counter.get_next_code()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.main_image and os.path.isfile(self.main_image.path):
            os.remove(self.main_image.path)
        for image in self.images.all():
            if image.image and os.path.isfile(image.image.path):
                os.remove(image.image.path)
            image.delete()
        super().delete(*args, **kwargs)


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

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    parent = models.ForeignKey(
        'self', null=True, blank=True, related_name='children', on_delete=models.CASCADE
    )
    key = models.CharField(max_length=50, verbose_name="Variant Key", help_text="مثل 'Color', 'Size', 'Type'")
    value = models.CharField(max_length=50, verbose_name="Variant Value", help_text="مثل 'Red', '42', 'Roasted'")
    sku = models.CharField(max_length=50, unique=True, verbose_name="SKU Code", blank=True, null=True)
    stock = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="Stock Quantity")
    price_override = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True, verbose_name="Custom Price")

    class Meta:
        unique_together = ('product', 'parent', 'key', 'value')
        verbose_name = "Product Variant"
        verbose_name_plural = "Product Variants"

    def __str__(self):
        names = [self.value]
        parent = self.parent
        while parent:
            names.append(parent.value)
            parent = parent.parent
        return f"{self.product.name} ({' > '.join(reversed(names))})"

    @property
    def final_price(self):
        return self.price_override if self.price_override else self.product.final_price

    def total_stock(self):
        """موجودی کل شامل تمام زیر واریانت‌ها"""
        if self.children.exists():
            return sum(child.total_stock() for child in self.children.all())
        return self.stock

    def generate_sku(self):
        """
        تولید خودکار SKU بر اساس زنجیرهٔ واریانت‌ها.
        مثال: P123-COLOR-RED-SIZE-42
        """
        parts = [f"P{self.product.id}"]

        # تمام واریانت‌های والد را از بالا به پایین جمع کن
        lineage = []
        current = self
        while current:
            lineage.append(f"{slugify(current.key).upper()}-{slugify(current.value).upper()}")
            current = current.parent

        # ترتیب را برعکس کن تا از ریشه تا برگ باشد
        parts.extend(reversed(lineage))

        base_sku = "-".join(parts)

        # در صورت نیاز برای اطمینان از یکتایی
        hash_suffix = hashlib.md5(base_sku.encode()).hexdigest()[:6].upper()
        return f"{base_sku}-{hash_suffix}"

    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = self.generate_sku()
        super().save(*args, **kwargs)