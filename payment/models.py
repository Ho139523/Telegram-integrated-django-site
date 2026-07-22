from decimal import Decimal
import logging
import uuid
from django.utils import timezone
from datetime import timedelta
import uuid

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import F
from django.utils import timezone

from accounts.models import ProfileModel

from products.models import (
    Product,
    Store,
    ProductVariant,
)

from payment.tasks import send_payment_notifications_task


logger = logging.getLogger(__name__)


# ============================================================
# CART
# ============================================================

class Cart(models.Model):

    profile = models.ForeignKey(
        ProfileModel,
        on_delete=models.CASCADE,
        related_name="carts",
        null=True,
        blank=True,
    )

    session_key = models.CharField(
        max_length=40,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):

        return (
            f"Cart {self.id} - "
            f"{self.profile if self.profile else 'Guest'}"
        )

    @property
    def total_items(self):

        return sum(
            item.quantity
            for item in self.items.all()
        )

    @property
    def total_price(self):

        return sum(
            item.total_price()
            for item in self.items.all()
        )

    def delete(self, *args, **kwargs):

        if self.transaction_set.filter(
            status="paid"
        ).exists():

            raise ValidationError(
                "سبد خرید پرداخت‌شده قابل حذف نیست"
            )

        super().delete(
            *args,
            **kwargs
        )


# ============================================================
# CART ITEM
# ============================================================

class CartItem(models.Model):

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
    )

    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="cart_items",
    )

    quantity = models.PositiveIntegerField(
        default=1,
        validators=[
            MinValueValidator(1)
        ],
    )

    class Meta:

        unique_together = (
            "cart",
            "product",
            "variant",
        )

        indexes = [

            models.Index(
                fields=["cart"]
            ),

            models.Index(
                fields=["product"]
            ),

            models.Index(
                fields=["variant"]
            ),

        ]

    def __str__(self):

        variant_info = (
            f" ({self.variant.sku})"
            if self.variant
            else ""
        )

        return (
            f"{self.quantity} x "
            f"{self.product.name}"
            f"{variant_info}"
        )

    @property
    def unit_price(self):

        if (
            self.variant
            and self.variant.price_override
        ):

            return (
                self.variant.price_override
            )

        return self.product.final_price

    def total_price(self):

        return (
            self.quantity
            * self.unit_price
        )

    def clean(self):

        product = self.product

        if (
            product.min_quantity
            and self.quantity
            < product.min_quantity
        ):

            raise ValidationError(
                f"حداقل مقدار خرید "
                f"{product.min_quantity} "
                f"{product.unit.symbol}"
            )

        if (
            product.max_quantity
            and self.quantity
            > product.max_quantity
        ):

            raise ValidationError(
                f"حداکثر مقدار خرید "
                f"{product.max_quantity} "
                f"{product.unit.symbol}"
            )

        if (
            product.quantity_step
            and (
                self.quantity
                % product.quantity_step
                != 0
            )
        ):

            raise ValidationError(
                f"مقدار خرید باید مضربی از "
                f"{product.quantity_step} "
                f"{product.unit.symbol}"
            )

        if self.variant:

            if (
                self.quantity
                > self.variant.stock
            ):

                raise ValidationError(
                    f"موجودی واریانت "
                    f"({self.variant.stock}) "
                    f"کافی نیست"
                )

        else:

            if (
                self.quantity
                > self.product.stock
            ):

                raise ValidationError(
                    f"موجودی محصول "
                    f"({self.product.stock}) "
                    f"کافی نیست"
                )

    def save(self, *args, **kwargs):

        self.clean()

        super().save(
            *args,
            **kwargs
        )

    def available_stock(self):

        if self.variant:

            return self.variant.stock

        return self.product.stock


# ============================================================
# TRANSACTION
# ============================================================
class Transaction(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("canceled", "Canceled"),
        ("refunded", "Refunded"),
    ]

    transaction_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    profile = models.ForeignKey(
        ProfileModel,
        on_delete=models.CASCADE,
        related_name="transactions"
    )

    cart = models.ForeignKey(
        Cart,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    currency = models.ForeignKey(
        "wallets.Currency",
        on_delete=models.PROTECT,
        related_name="transactions",
    )

    authority = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True
    )

    amount = models.PositiveIntegerField()

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="pending"
    )

    zarinpal_ref_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="کد پیگیری زرین‌پال"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):

        return (
            f"Transaction "
            f"{self.transaction_id} - "
            f"{self.profile.fname} "
            f"{self.profile.lname} - "
            f"{self.status}"
        )



# ============================================================
# SALE
# ============================================================

class Sale(models.Model):

    sale_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
    )

    operation_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name="sales"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    seller = models.ForeignKey(
        Store,
        on_delete=models.CASCADE
    )

    quantity = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    unit_price = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    currency = models.ForeignKey(
        "wallets.Currency",
        on_delete=models.PROTECT,
        related_name="sales",
    )

    total_price = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    # =====================================================
    # RETURN POLICY SNAPSHOT
    # =====================================================

    return_period_days = models.PositiveIntegerField(
        verbose_name="مدت مجاز مرجوعی در زمان فروش"
    )

    release_at = models.DateTimeField(
        verbose_name="زمان آزاد شدن مبلغ فروشنده"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return (
            f"Sale: "
            f"{self.product.name} - "
            f"{self.quantity} x "
            f"{self.unit_price}"
        )

    @property
    def is_release_due(self):

        return timezone.now() >= self.release_at

    # =====================================================
    # FACTORY
    # =====================================================

    @classmethod
    def create_from_store(
        cls,
        *,
        transaction,
        product,
        seller,
        quantity,
        unit_price,
        total_price,
        variant=None,
    ):

        created_at = timezone.now()

        return_period_days = (
            seller.return_period_days
        )

        release_at = (
            created_at
            + timedelta(
                days=return_period_days
            )
        )

        return cls.objects.create(
            transaction=transaction,
            product=product,
            variant=variant,
            seller=seller,

            currency=transaction.currency,

            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price,

            return_period_days=return_period_days,
            release_at=release_at,
        )


