# wallets/services/sale_pending.py

from decimal import Decimal

from django.db import transaction

from wallets.models import (
    WalletBalance,
    WalletEntry,
)


@transaction.atomic
def sale_pending(
    *,
    seller_wallet,
    currency,
    amount: Decimal,
    reference_id=None,
):

    if amount <= 0:
        raise ValueError(
            "Amount must be positive."
        )

    balance, _ = (
        WalletBalance.objects
        .select_for_update()
        .get_or_create(
            wallet=seller_wallet,
            currency=currency,
        )
    )

    balance.pending += amount

    balance.save(
        update_fields=["pending"]
    )

    return WalletEntry.objects.create(
        wallet=seller_wallet,
        currency=currency,
        amount=amount,
        type=WalletEntry.Type.SALE_PENDING,
        reference_id=reference_id,
    )
