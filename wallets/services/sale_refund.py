# wallets/services/sale_refund.py

from decimal import Decimal

from django.db import transaction

from wallets.models import (
    WalletBalance,
    WalletEntry,
)


@transaction.atomic
def sale_refund(
    *,
    seller_wallet,
    buyer_wallet,
    currency,
    amount: Decimal,
    reference_id=None,
):

    seller_balance = (
        WalletBalance.objects
        .select_for_update()
        .get(
            wallet=seller_wallet,
            currency=currency,
        )
    )

    if seller_balance.pending < amount:
        raise ValueError(
            "Insufficient pending balance."
        )

    buyer_balance, _ = (
        WalletBalance.objects
        .select_for_update()
        .get_or_create(
            wallet=buyer_wallet,
            currency=currency,
        )
    )

    seller_balance.pending -= amount
    buyer_balance.available += amount

    seller_balance.save(
        update_fields=["pending"]
    )

    buyer_balance.save(
        update_fields=["available"]
    )

    WalletEntry.objects.create(
        wallet=seller_wallet,
        currency=currency,
        amount=-amount,
        type=WalletEntry.Type.SALE_REFUND,
        reference_id=reference_id,
    )

    WalletEntry.objects.create(
        wallet=buyer_wallet,
        currency=currency,
        amount=amount,
        type=WalletEntry.Type.REFUND,
        reference_id=reference_id,
    )
