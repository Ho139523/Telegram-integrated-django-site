from django.db import models

from wallets.models.currency import Currency


class ExchangeRate(models.Model):

    from_currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name="outgoing_rates",
    )

    to_currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name="incoming_rates",
    )

    rate = models.DecimalField(
        max_digits=30,
        decimal_places=12,
    )

    source = models.CharField(
        max_length=50,
        default="manual",
    )

    fetched_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:

        unique_together = (
            "from_currency",
            "to_currency",
        )

        indexes = [
            models.Index(
                fields=[
                    "from_currency",
                    "to_currency",
                ]
            ),
        ]

    def __str__(self):

        return (
            f"1 {self.from_currency.code} = "
            f"{self.rate} {self.to_currency.code}"
        )
