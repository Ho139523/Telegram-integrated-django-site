# wallets/services/deposit.py

from decimal import Decimal
from wallets.services.utils import operation_exists
from django.db import transaction

from wallets.models import (
    WalletBalance,
    WalletEntry,
)


@transaction.atomic
def deposit(
    *,
    wallet,
    currency,
    amount,
    description="",
    reference_id=None,
    operation_id=None,
):
    if operation_exists(
        operation_id=operation_id,
        entry_type=WalletEntry.Type.DEPOSIT,
    ):
        return

    if amount <= 0:
        raise ValueError(
            "Deposit amount must be positive."
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

    entry = WalletEntry.objects.create(
        wallet=wallet,
        currency=currency,
        amount=amount,
        type=WalletEntry.Type.DEPOSIT,
        description=description,
        reference_id=reference_id,
        operation_id=operation_id,
    )

    return entry
