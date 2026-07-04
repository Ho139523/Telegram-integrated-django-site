# wallets/services/platform.py

from django.conf import settings

from wallets.models import Wallet


def get_platform_wallet():

    wallet_id = getattr(
        settings,
        "PLATFORM_WALLET_ID",
        None,
    )

    if wallet_id is None:
        raise RuntimeError(
            "PLATFORM_WALLET_ID is not configured."
        )

    return Wallet.objects.get(
        pk=wallet_id
    )
