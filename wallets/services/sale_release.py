# wallets/services/sale_release.py

from decimal import Decimal
from wallets.services.utils import operation_exists
from django.db import transaction

from wallets.models import (
    WalletBalance,
    WalletEntry,
)

from wallets.services.treasury import (
    get_treasury_wallet,
)


@transaction.atomic
def sale_release(
    *,
    seller_wallet,
    currency,
    amount: Decimal,
    commission: Decimal,
    reference_id=None,
    operation_id=None,
):

    if operation_exists(
        operation_id=operation_id,
        entry_type=WalletEntry.Type.SALE_RELEASE,
    ):
        return
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

    if commission < 0:
        raise ValueError(
            "Commission cannot be negative."
        )

    net_amount = amount - commission

    if net_amount < 0:
        raise ValueError(
            "Commission cannot exceed amount."
        )

    treasury_wallet = get_treasury_wallet()

    treasury_balance, _ = (
        WalletBalance.objects
        .select_for_update()
        .get_or_create(
            wallet=treasury_wallet,
            currency=currency,
        )
    )

    # آزادسازی مبلغ فروشنده
    seller_balance.pending -= amount
    seller_balance.available += net_amount

    seller_balance.save(
        update_fields=[
            "pending",
            "available",
        ]
    )

    # انتقال کارمزد به خزانه
    if commission > 0:

        treasury_balance.available += commission

        treasury_balance.save(
            update_fields=[
                "available"
            ]
        )

    # ثبت رویداد فروش برای فروشنده
    WalletEntry.objects.create(
        wallet=seller_wallet,
        currency=currency,
        amount=amount,
        type=WalletEntry.Type.SALE_RELEASE,
        reference_id=reference_id,
        description="Sale released",
    )

    # ثبت دریافت کارمزد برای خزانه
    if commission > 0:

        WalletEntry.objects.create(
            wallet=treasury_wallet,
            currency=currency,
            amount=commission,
            type=WalletEntry.Type.COMMISSION,
            reference_id=reference_id,
            description="Platform commission received",
            operation_id=operation_id,
        )
