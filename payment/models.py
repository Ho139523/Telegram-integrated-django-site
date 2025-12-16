from django.db import models
from django.contrib.auth import get_user_model
from products.models import (
    Product, Store, ProductAttribute, ProductCodeCounter, ProductImage,
    ProductOption, ProductOptionValue, ProductVariant
    )
import uuid
from accounts.models import ProfileModel
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
import logging
from payment.tasks import send_payment_notifications_task

logger = logging.getLogger(__name__)


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

    def __str__(self):
        return f"Cart {self.id} - {self.profile if self.profile else 'Guest'}"

    def total_items(self):
        """تعداد کل آیتم‌ها در سبد خرید"""
        return sum(item.quantity for item in self.items.all())

    def total_price(self):
        """جمع کل مبلغ سبد خرید با احتساب واریانت‌ها"""
        return sum(item.total_price() for item in self.items.all())

    def get_sellers_split(self):
        sellers_split = {}

        items = self.items.select_related("product__store")

        for item in items:
            seller = item.product.store
            amount = item.total_price()
            sellers_split[seller] = sellers_split.get(seller, 0) + amount

        return sellers_split

    def delete(self, *args, **kwargs):
        if self.transaction_set.filter(status="paid").exists():
            raise ValidationError("سبد خرید پرداخت‌شده قابل حذف نیست")
        super().delete(*args, **kwargs)


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
        indexes = [
            models.Index(fields=["cart"]),
            models.Index(fields=["product"]),
            models.Index(fields=["variant"]),
        ]

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
            raise ValidationError(
                f"حداقل مقدار خرید {product.min_quantity} {product.unit.symbol}"
            )

        if product.max_quantity and self.quantity > product.max_quantity:
            raise ValidationError(
                f"حداکثر مقدار خرید {product.max_quantity} {product.unit.symbol}"
            )

        if product.quantity_step and (self.quantity % product.quantity_step != 0):
            raise ValidationError(
                f"مقدار خرید باید مضربی از {product.quantity_step} {product.unit.symbol} باشد"
            )

        if self.variant:
            if self.quantity > self.variant.stock:
                raise ValidationError(
                    f"موجودی واریانت ({self.variant.stock}) کافی نیست"
                )
        else:
            if self.quantity > self.product.stock:
                raise ValidationError(
                    f"موجودی محصول ({self.product.stock}) کافی نیست"
                )



    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def available_stock(self):
        if self.variant:
            return self.variant.stock
        return self.product.stock


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


    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.profile.fname} {self.profile.lname} - {self.status}"

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
    
    def finalize(self):
        """
        - قفل cart
        - جلوگیری از oversell
        - کسر موجودی
        - ایجاد Sale
        - ایجاد SplitPayment
        """
        self.refresh_from_db()
        if self.status == "paid":
            raise ValidationError("این تراکنش قبلاً پرداخت شده است")
        
        if not self.cart:
            raise ValidationError("سبد خرید وجود ندارد")

        with transaction.atomic():

            # قفل cart
            cart = (
                Cart.objects
                .select_for_update()
                .prefetch_related("items__variant", "items__product")
                .get(id=self.cart.id)
            )

            # قفل تمام واریانت‌ها
            variant_ids = [
                item.variant_id
                for item in cart.items.all()
                if item.variant_id
            ]

            variants = {
                v.id: v
                for v in ProductVariant.objects
                .select_for_update()
                .filter(id__in=variant_ids)
            }

            # بررسی موجودی
            for item in cart.items.all():
                if item.variant:
                    variant = variants[item.variant.id]
                    if variant.stock < item.quantity:
                        raise ValidationError(
                            f"موجودی واریانت {variant.sku} کافی نیست"
                        )
                else:
                    if item.product.stock < item.quantity:
                        raise ValidationError(
                            f"موجودی محصول {item.product.name} کافی نیست"
                        )

            # کسر موجودی + ایجاد Sale
            for item in cart.items.all():

                unit_price = item.unit_price
                total_price = unit_price * item.quantity

                if item.variant:
                    variant = variants[item.variant.id]
                    variant.stock = F("stock") - item.quantity
                    variant.save(update_fields=["stock"])

                Sale.objects.create(
                    transaction=self,
                    product=item.product,
                    variant=item.variant,
                    seller=item.product.store,
                    quantity=item.quantity,
                    unit_price=unit_price,
                    total_price=total_price,
                )

            # ایجاد split payment
            self.create_split_payments()

            # وضعیت پرداخت
            self.status = "paid"
            self.save(update_fields=["status"])
        
        send_payment_notifications_task.delay(transaction.id)
        logger.info(f"Transaction {self.id} finalized: amount={self.amount}, profile={self.profile_id}, cart={self.cart_id}")
    
    async def finalize_async(self, redis_url="redis://localhost:6379"):
        """
        Async finalize با استفاده از Redis lock
        """
        import aioredis
        from asgiref.sync import sync_to_async

        redis = await aioredis.from_url(redis_url)
        lock_key = f"transaction_lock:{self.id}"  # کلید lock مخصوص این تراکنش

        # استفاده از lock با timeout
        async with redis.lock(lock_key, timeout=30):  # lock حداکثر 30 ثانیه
            # دوباره fetch کردن تراکنش به صورت sync -> async
            txn = await sync_to_async(Transaction.objects.select_for_update().get)(id=self.id)
            
            if txn.status == "paid":
                raise ValidationError("این تراکنش قبلاً پرداخت شده است")

            if not txn.cart:
                raise ValidationError("سبد خرید وجود ندارد")

            # قفل واریانت‌ها و محصولات + بررسی موجودی و ایجاد Sale
            await sync_to_async(txn.finalize)()  # استفاده از متد finalize موجود

    def refund(self):
        if self.status != "paid":
            raise ValidationError("فقط تراکنش پرداخت‌شده قابل مرجوع است")
        
        with transaction.atomic():
            # برگرداندن موجودی
            for sale in self.sales.select_related("product", "variant").all():
                if sale.variant:
                    sale.variant.stock = F("stock") + sale.quantity
                    sale.variant.save(update_fields=["stock"])
                else:
                    sale.product.stock = F("stock") + sale.quantity
                    sale.product.save(update_fields=["stock"])
            
            # mark split payments as unpaid
            self.split_payments.update(is_paid=False, paid_at=None)
            
            # mark transaction as refunded
            self.status = "refunded"
            self.save(update_fields=["status", "updated_at"])

            # Optional: mark sales as refunded (برای گزارش)
            self.sales.update(total_price=0)

        logger.info(f"Transaction {self.id} refunded: amount={self.amount}, profile={self.profile_id}")



class Sale(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name="sales")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    seller = models.ForeignKey(Store, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(null=True, blank=True)
    unit_price = models.PositiveIntegerField(null=True, blank=True)
    total_price = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"Sale: {self.product.name} - {self.quantity} x {self.unit_price}"
