from django.db import models

from wallets.models.wallet import Wallet
from wallets.models.currency import Currency


class Withdrawal(models.Model):

    class Status(models.TextChoices):

        PENDING = "pending", "Pending"

        PROCESSING = "processing", "Processing"

        COMPLETED = "completed", "Completed"

        FAILED = "failed", "Failed"

        CANCELED = "canceled", "Canceled"

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name="withdrawals"
    )

    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT
    )

    amount = models.DecimalField(
        max_digits=30,
        decimal_places=8
    )

    fee = models.DecimalField(
        max_digits=30,
        decimal_places=8,
        default=0
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    provider = models.CharField(
        max_length=100,
        blank=True,
        default=""
    )

    destination = models.TextField(
        blank=True,
        default=""
    )

    external_reference = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    processed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    operation_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
    )

    class Meta:

        ordering = [
            "-created_at"
        ]

        indexes = [
            models.Index(
                fields=["status"]
            ),

            models.Index(
                fields=["created_at"]
            ),

            models.Index(
                fields=["wallet"]
            ),
        ]

    def __str__(self):
        return (
            f"{self.amount} "
            f"{self.currency_id} "
            f"({self.status})"
        )
