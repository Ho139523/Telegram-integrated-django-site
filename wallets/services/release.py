# wallets/services/release.py

from decimal import Decimal
from wallets.services.utils import operation_exists
from django.db import transaction

from wallets.models import (
    WalletBalance,
    WalletEntry,
)


@transaction.atomic
def release(
    *,
    wallet,
    currency,
    amount: Decimal,
    to_pending=False,
    description="",
    reference_id=None,
    operation_id=None,
):

    if operation_exists(
        operation_id=operation_id,
        entry_type=WalletEntry.Type.RELEASE,
    ):
        return

    balance = (
        WalletBalance.objects
        .select_for_update()
        .get(
            wallet=wallet,
            currency=currency,
        )
    )

    if balance.locked < amount:
        raise ValueError(
            "Insufficient locked balance."
        )

    balance.locked -= amount

    if to_pending:
        balance.pending += amount
    else:
        balance.available += amount

    balance.save()

    return WalletEntry.objects.create(
        wallet=wallet,
        currency=currency,
        amount=amount,
        type=WalletEntry.Type.RELEASE,
        description=description,
        reference_id=reference_id,
        operation_id=operation_id,
    )
