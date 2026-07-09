# wallets/services/withdrawal.py

from decimal import Decimal
from wallets.services.utils import operation_exists
from django.db import transaction

from wallets.models import (
    WalletBalance,
    WalletEntry,
    Withdrawal,
)


@transaction.atomic
def withdraw(
    *,
    wallet,
    currency,
    amount: Decimal,
    provider: str,
    destination: str,
    fee: Decimal = Decimal("0"),
    operation_id=None,
):

    if operation_exists(
        operation_id=operation_id,
        entry_type=WalletEntry.Type.WITHDRAW,
    ):
        return
    total_amount = amount + fee

    balance = (
        WalletBalance.objects
        .select_for_update()
        .get(
            wallet=wallet,
            currency=currency,
        )
    )

    if balance.available < total_amount:
        raise ValueError(
            "Insufficient balance."
        )

    balance.available -= total_amount
    balance.locked += total_amount

    balance.save(
        update_fields=[
            "available",
            "locked",
        ]
    )

    withdrawal = Withdrawal.objects.create(
        wallet=wallet,
        currency=currency,
        amount=amount,
        fee=fee,
        provider=provider,
        destination=destination,
    )

    WalletEntry.objects.create(
        wallet=wallet,
        currency=currency,
        amount=-total_amount,
        type=WalletEntry.Type.WITHDRAW,
        description=f"Withdrawal #{withdrawal.pk}",
        operation_id=operation_id,
    )

    return withdrawal
