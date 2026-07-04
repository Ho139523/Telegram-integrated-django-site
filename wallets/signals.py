# wallets/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import ProfileModel
from wallets.models import Wallet


@receiver(post_save, sender=ProfileModel)
def create_wallet(sender, instance, created, **kwargs):
    """
    Automatically create a wallet for every new profile.
    """

    if created:
        Wallet.objects.get_or_create(
            profile=instance
        )
