# wallets/models/wallet.p
from django.db import models
from accounts.models import ProfileModel


class Wallet(models.Model):

    profile = models.OneToOneField(
        ProfileModel,
        on_delete=models.CASCADE,
        related_name="wallet",
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    is_active = models.BooleanField(
        default=True
    )

    def __str__(self):
        return f"Wallet<{self.profile}>"



