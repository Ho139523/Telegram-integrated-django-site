from wallets.models import Wallet
from wallets.models import Currency
from django.db import models


class WalletBalance(models.Model):

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name="balances"
    )

    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT
    )

    available = models.DecimalField(
        max_digits=30,
        decimal_places=8,
        default=0
    )

    pending = models.DecimalField(
        max_digits=30,
        decimal_places=8,
        default=0
    )

    locked = models.DecimalField(
        max_digits=30,
        decimal_places=8,
        default=0
    )


    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=["wallet", "currency"],
                name="unique_wallet_currency"
            )
        ]


    def __str__(self):
        return (
            f"{self.wallet.profile} - "
            f"{self.currency_id}"
        )
