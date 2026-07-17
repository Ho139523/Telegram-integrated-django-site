# wallets/services/sale_refund.py

from django.db import transaction
from wallets.events.publisher import EventPublisher

from wallets.constants import Services

from wallets.models import WalletEntry

from wallets.services.base import (
    get_balance,
    log_entry,
    ensure_balance,
    validate_positive,
)

from wallets.services.decorators import idempotent

from wallets.events.factory import EventFactory


@transaction.atomic
@idempotent(Services.SALE_REFUND)
def sale_refund(
    *,
    seller_wallet,
    buyer_wallet,
    currency,
    amount,
    reference_id=None,
    operation_id=None,
):

    validate_positive(amount)

    seller = get_balance(
        wallet=seller_wallet,
        currency=currency,
    )

    ensure_balance(
        seller,
        "pending",
        amount,
    )

    buyer = get_balance(
        wallet=buyer_wallet,
        currency=currency,
        create=True,
    )

    seller.pending -= amount
    buyer.available += amount

    seller.save(
        update_fields=[
            "pending",
        ]
    )

    buyer.save(
        update_fields=[
            "available",
        ]
    )

    seller_entry = log_entry(
        wallet=seller_wallet,
        currency=currency,
        amount=-amount,
        entry_type=WalletEntry.Type.SALE_REFUND,
        reference_id=reference_id,
        operation_id=operation_id,
        description="Sale refunded",
    )

    buyer_entry = log_entry(
        wallet=buyer_wallet,
        currency=currency,
        amount=amount,
        entry_type=WalletEntry.Type.REFUND,
        reference_id=reference_id,
        operation_id=operation_id,
        description="Refund received",
    )

    EventPublisher.publish(
        EventFactory.sale_refund(
            seller_entry=seller_entry,
            buyer_entry=buyer_entry,
        )
    )

    return buyer_entry
