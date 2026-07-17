# wallets/services/sale_release.py

from django.db import transaction

from wallets.constants import Services
from wallets.models import WalletEntry

from wallets.services.base import (
    get_balance,
    log_entry,
    ensure_balance,
    validate_positive,
)

from wallets.services.treasury import (
    get_treasury_wallet,
)

from wallets.services.decorators import idempotent

from wallets.events.factory import EventFactory
from wallets.events.publisher import EventPublisher


@transaction.atomic
@idempotent(Services.SALE_RELEASE)
def sale_release(
    *,
    seller_wallet,
    currency,
    amount,
    commission,
    reference_id=None,
    operation_id=None,
):

    validate_positive(amount)

    if commission < 0:
        raise ValueError(
            "Commission cannot be negative."
        )

    net = amount - commission

    if net < 0:
        raise ValueError(
            "Commission cannot exceed amount."
        )

    seller = get_balance(
        wallet=seller_wallet,
        currency=currency,
    )

    ensure_balance(
        seller,
        "pending",
        amount,
    )

    treasury = get_balance(
        wallet=get_treasury_wallet(),
        currency=currency,
        create=True,
    )

    seller.pending -= amount
    seller.available += net

    seller.save(
        update_fields=[
            "pending",
            "available",
        ]
    )

    if commission:
        treasury.available += commission

        treasury.save(
            update_fields=[
                "available",
            ]
        )

    seller_entry = log_entry(
        wallet=seller_wallet,
        currency=currency,
        amount=amount,
        entry_type=WalletEntry.Type.SALE_RELEASE,
        reference_id=reference_id,
        operation_id=operation_id,
        description="Sale released",
    )

    if commission:
        log_entry(
            wallet=treasury.wallet,
            currency=currency,
            amount=commission,
            entry_type=WalletEntry.Type.COMMISSION,
            reference_id=reference_id,
            operation_id=operation_id,
            description="Platform commission received",
        )

    EventPublisher.publish(
        EventFactory.sale_release(
            seller_entry,
            commission=commission,
        )
    )

    return seller_entry
