# wallets/services/refund.py

from decimal import Decimal

from django.db import transaction

from wallets.models import (
    WalletBalance,
    WalletEntry,
)


@transaction.atomic
def refund(
    *,
    wallet,
    currency,
    amount: Decimal,
    description="",
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
            wallet=wallet,
            currency=currency,
        )
    )

    balance.available += amount

    balance.save(
        update_fields=["available"]
    )

    return WalletEntry.objects.create(
        wallet=wallet,
        currency=currency,
        amount=amount,
        type=WalletEntry.Type.REFUND,
        description=description,
        reference_id=reference_id,
    )
