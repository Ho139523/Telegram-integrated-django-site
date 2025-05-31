from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product, Store  # Ensure you have a Product model
import uuid
from accounts.models import ProfileModel
from django.core.validators import MinValueValidator


User = get_user_model()


from products.models import Product

class Cart(models.Model):
    profile = models.ForeignKey(ProfileModel, on_delete=models.CASCADE, related_name="carts", null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)  # برای کاربران غیر لاگین
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart {self.id} - {self.profile if self.profile else 'Guest'}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    def total_price(self):
        return self.quantity * self.product.final_price  # فرض کنید محصول قیمت دارد

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Cart {self.cart.id}"


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
