from django.db import models
from wallets.models.wallet import Wallet
from wallets.models.currency import Currency


class WalletEntry(models.Model):

    class Type(models.TextChoices):

        DEPOSIT = "deposit", "Deposit"

        PURCHASE = "purchase", "Purchase"

        SALE_PENDING = "sale_pending", "Sale Pending"

        SALE_RELEASE = "sale_release", "Sale Release"

        SALE_REFUND = "sale_refund", "Sale Refund"

        REFUND = "refund", "Refund"

        WITHDRAW = "withdraw", "Withdraw"

        TRANSFER_IN = "transfer_in", "Transfer In"

        TRANSFER_OUT = "transfer_out", "Transfer Out"

        HOLD = "hold", "Hold"

        RELEASE = "release", "Release"

        COMMISSION = "commission", "Commission"

        CONVERSION = "conversion", "Conversion"

        ADJUSTMENT = "adjustment", "Adjustment"


    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT
    )

    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT
    )

    type = models.CharField(
        max_length=30,
        choices=Type.choices
    )

    amount = models.DecimalField(
        max_digits=30,
        decimal_places=8
    )

    description = models.TextField(
        blank=True
    )

    reference_id = models.UUIDField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["wallet"]),
            models.Index(fields=["currency"]),
            models.Index(fields=["type"]),
            models.Index(fields=["created_at"]),

            models.Index(
                fields=["wallet", "created_at"]
            ),
        ]

    def __str__(self):
        return (
            f"{self.type}: "
            f"{self.amount} "
            f"{self.currency_id}"
        )
