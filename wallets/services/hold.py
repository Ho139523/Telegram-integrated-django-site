# wallets/services/hold.py

from decimal import Decimal

from django.db import transaction

from wallets.models import (
    WalletBalance,
    WalletEntry,
)


@transaction.atomic
def hold(
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

    balance = (
        WalletBalance.objects
        .select_for_update()
        .get(
            wallet=wallet,
            currency=currency,
        )
    )

    if balance.available < amount:
        raise ValueError(
            "Insufficient balance."
        )

    balance.available -= amount
    balance.locked += amount

    balance.save(
        update_fields=[
            "available",
            "locked",
        ]
    )

    return WalletEntry.objects.create(
        wallet=wallet,
        currency=currency,
        amount=amount,
        type=WalletEntry.Type.HOLD,
        description=description,
        reference_id=reference_id,
    )
