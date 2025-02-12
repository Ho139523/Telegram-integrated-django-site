from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product, Store  # Ensure you have a Product model
import uuid
from accounts.models import ProfileModel

User = get_user_model()

class Transaction(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),       # درخواست ارسال شده، منتظر پرداخت
        ("paid", "Paid"),             # پرداخت انجام شده
        ("failed", "Failed"),         # پرداخت ناموفق
        ("canceled", "Canceled"),     # کاربر پرداخت را لغو کرده
        ("refunded", "Refunded"),     # بازگشت وجه
    ]

    # Unique identifier for tracking payments
    transaction_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    profile = models.ForeignKey(ProfileModel, on_delete=models.CASCADE, related_name="transactions")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions")
    
    authority = models.CharField(max_length=50, unique=True, null=True, blank=True)  # Unique authority from ZarinPal
    amount = models.PositiveIntegerField()  # Amount in Tomans (stored in smallest unit)
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
    seller = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="sales", verbose_name="Seller")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sales", verbose_name="Product")
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name="sale", verbose_name="Transaction")
    amount = models.PositiveIntegerField(verbose_name="Amount")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Sale Date")

    def __str__(self):
        return f"Sale: {self.product.name} - {self.seller.name} - {self.amount} تومان"
