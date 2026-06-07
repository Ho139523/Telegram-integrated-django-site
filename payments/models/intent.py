import uuid
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone


class PaymentIntent(models.Model):

    STATUS = [
        ("created", "Created"),
        ("processing", "Processing"),
        ("succeeded", "Succeeded"),
        ("failed", "Failed"),
        ("expired", "Expired"),
        ("canceled", "Canceled"),
        ("refunded", "Refunded"),
    ]

    intent_id = models.UUIDField(default=uuid.uuid4, unique=True)

    profile = models.ForeignKey(
        "accounts.ProfileModel",
        on_delete=models.CASCADE
    )

    amount = models.BigIntegerField()

    currency = models.CharField(max_length=10, default="IRR")

    status = models.CharField(
        max_length=30,
        choices=STATUS,
        default="created"
    )

    gateway = models.CharField(max_length=50)

    # 🔥 Polymorphic Target
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
    )
    object_id = models.PositiveIntegerField()
    target = GenericForeignKey()

    metadata = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.intent_id} - {self.amount}"

    @property
    def is_expired(self):
    
        if self.status in (
            "succeeded",
            "canceled",
            "failed",
            "refunded"
        ):
            return False
    
        if not self.expires_at:
            return False
    
        return timezone.now() >= self.expires_at


    def mark_expired(self):
        if self.status == "created":
            self.status = "expired"
            self.save(update_fields=["status"])

    
