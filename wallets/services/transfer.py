# wallets/services/transfer.py

from decimal import Decimal

from django.db import transaction

from wallets.models import (
    WalletBalance,
    WalletEntry,
)


@transaction.atomic
def transfer(
    *,
    from_wallet,
    to_wallet,
    currency,
    amount: Decimal,
    description="",
    reference_id=None,
):

    if from_wallet.pk == to_wallet.pk:
        raise ValueError(
            "Cannot transfer to yourself."
        )

    sender = (
        WalletBalance.objects
        .select_for_update()
        .get(
            wallet=from_wallet,
            currency=currency,
        )
    )

    receiver, _ = (
        WalletBalance.objects
        .select_for_update()
        .get_or_create(
            wallet=to_wallet,
            currency=currency,
        )
    )

    if sender.available < amount:
        raise ValueError(
            "Insufficient balance."
        )

    sender.available -= amount
    receiver.available += amount

    sender.save(update_fields=["available"])
    receiver.save(update_fields=["available"])

    WalletEntry.objects.create(
        wallet=from_wallet,
        currency=currency,
        amount=-amount,
        type=WalletEntry.Type.TRANSFER_OUT,
        description=description,
        reference_id=reference_id,
    )

    return WalletEntry.objects.create(
        wallet=to_wallet,
        currency=currency,
        amount=amount,
        type=WalletEntry.Type.TRANSFER_IN,
        description=description,
        reference_id=reference_id,
    )
