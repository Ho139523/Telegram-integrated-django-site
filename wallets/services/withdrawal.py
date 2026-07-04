# wallets/services/withdrawal.py

from decimal import Decimal

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
):

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
    )

    return withdrawal
