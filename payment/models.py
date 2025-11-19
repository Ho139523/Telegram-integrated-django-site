from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product, Store  # Ensure you have a Product model
import uuid
from accounts.models import ProfileModel
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError


User = get_user_model()


from products.models import Product


class SplitPayment(models.Model):
    """مدیریت تقسیم پرداخت بین چندین فروشنده"""
    transaction = models.ForeignKey('Transaction', on_delete=models.CASCADE, related_name='split_payments')
    seller = models.ForeignKey(Store, on_delete=models.CASCADE, verbose_name='فروشنده')
    amount = models.PositiveIntegerField(verbose_name='مبلغ قابل پرداخت به فروشنده')
    is_paid = models.BooleanField(default=False, verbose_name='پرداخت شده')
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ پرداخت')
    
    class Meta:
        verbose_name = "تقسیم پرداخت"
        verbose_name_plural = "تقسیم‌های پرداخت"
    
    def __str__(self):
        return f"{self.seller.name} - {self.amount} تومان"


class Cart(models.Model):
    profile = models.ForeignKey(ProfileModel, on_delete=models.CASCADE, related_name="carts", null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)  # برای کاربران غیر لاگین
    created_at = models.DateTimeField(auto_now_add=True)

    def total_items(self):
        """تعداد کل آیتم‌ها در سبد خرید"""
        return sum(item.quantity for item in self.items.all())

    def total_price(self):
        """جمع کل مبلغ سبد خرید با احتساب واریانت‌ها"""
        return sum(item.total_price() for item in self.items.all())

    def get_sellers_split(self):
        """محاسبه سهم هر فروشنده از سبد خرید"""
        sellers_split = {}
        for item in self.items.all():
            seller = item.product.store
            amount = item.total_price()
            if seller not in sellers_split:
                sellers_split[seller] = 0
            sellers_split[seller] += amount
        return sellers_split


    def __str__(self):
        return f"Cart {self.id} - {self.profile if self.profile else 'Guest'}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="cart_items"
    )
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        unique_together = ("cart", "product", "variant")

    def __str__(self):
        variant_info = f" ({self.variant.sku})" if self.variant else ""
        return f"{self.quantity} x {self.product.name}{variant_info}"

    @property
    def unit_price(self):
        if self.variant and self.variant.price_override:
            return self.variant.price_override
        return self.product.final_price

    def total_price(self):
        return self.quantity * self.unit_price

    def clean(self):
        product = self.product

        if product.min_quantity and self.quantity < product.min_quantity:
            raise ValidationError(f"حداقل مقدار خرید برای این کالا {product.min_quantity} {product.unit.symbol} است.")

        if product.max_quantity and self.quantity > product.max_quantity:
            raise ValidationError(f"حداکثر مقدار خرید برای این کالا {product.max_quantity} {product.unit.symbol} است.")

        if product.quantity_step and (self.quantity % product.quantity_step != 0):
            raise ValidationError(f"مقدار خرید باید مضربی از {product.quantity_step} {product.unit.symbol} باشد.")

        if self.variant:
            if self.quantity > self.variant.total_stock():
                raise ValidationError(f"موجودی واریانت انتخاب‌شده ({self.variant.total_stock()}) کافی نیست.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def available_stock(self):
        """موجودی قابل خرید برای این آیتم"""
        if self.variant:
            return self.variant.stock
        return self.product.total_stock()


class Transaction(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("canceled", "Canceled"),
        ("refunded", "Refunded"),
    ]

    transaction_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    profile = models.ForeignKey(ProfileModel, on_delete=models.CASCADE, related_name="transactions")
    cart = models.ForeignKey(Cart, on_delete=models.SET_NULL, null=True, blank=True)  # تغییر از Product به Cart
    authority = models.CharField(max_length=50, unique=True, null=True, blank=True)
    amount = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    zarinpal_ref_id = models.CharField(max_length=100, null=True, blank=True, verbose_name="کد پیگیری زرین‌پال")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def mark_as_paid(self):
        """Mark transaction as paid."""
        self.status = "paid"
        self.save()

    def mark_as_failed(self):
        """Mark transaction as failed."""
        self.status = "failed"
        self.save()

    def mark_as_canceled(self):
        """Mark transaction as canceled."""
        self.status = "canceled"
        self.save()

    def mark_as_refunded(self):
        """Mark transaction as refunded."""
        self.status = "refunded"
        self.save()

    def create_split_payments(self):
        """ایجاد رکوردهای تقسیم پرداخت برای این تراکنش"""
        if not self.cart:
            return
        
        sellers_split = self.cart.get_sellers_split()
        for seller, amount in sellers_split.items():
            SplitPayment.objects.create(
                transaction=self,
                seller=seller,
                amount=amount
            )

    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.profile.fname} {self.profile.lname} - {self.status}"




class Sale(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name="sales")  # تغییر از OneToOne به ForeignKey
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    seller = models.ForeignKey(Store, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(null=True, blank=True)
    unit_price = models.PositiveIntegerField(null=True, blank=True)  # قیمت واحد در زمان خرید
    total_price = models.PositiveIntegerField(null=True, blank=True)  # قیمت کل (quantity * unit_price)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sale: {self.product.name} - {self.quantity} x {self.unit_price}"
