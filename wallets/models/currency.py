from django.db import models



class Currency(models.Model):
    code = models.CharField(
        max_length=3,
        primary_key=True,
    )

    name = models.CharField(max_length=100)

    symbol = models.CharField(max_length=10)

    decimals = models.PositiveSmallIntegerField(default=2)

    is_active = models.BooleanField(default=True)

    is_crypto = models.BooleanField(default=False)

    def __str__(self):
        return self.code
