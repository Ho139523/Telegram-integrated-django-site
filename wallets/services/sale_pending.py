# wallets/services/sale_pending.py

from django.db import transaction

from wallets.events.publisher import EventPublisher

from wallets.constants import Services

from wallets.models import WalletEntry

from wallets.services.base import (
    get_balance,
    ensure_balance,
    log_entry,
    validate_positive,
)

from wallets.services.decorators import idempotent

from wallets.events.factory import EventFactory


@transaction.atomic
@idempotent(Services.SALE_PENDING)
def sale_pending(
    *,
    seller_wallet,
    currency,
    amount,
    reference_id=None,
    operation_id=None,
):

    validate_positive(amount)

    balance = get_balance(
        wallet=seller_wallet,
        currency=currency,
    )

    ensure_balance(
        balance,
        "available",
        amount,
    )

    balance.available -= amount
    balance.pending += amount

    balance.save(
        update_fields=[
            "available",
            "pending",
        ]
    )

    entry = log_entry(
        wallet=seller_wallet,
        currency=currency,
        amount=amount,
        entry_type=WalletEntry.Type.SALE_PENDING,
        reference_id=reference_id,
        operation_id=operation_id,
        description="Sale pending",
    )

    EventPublisher.publish(
        EventFactory.sale_pending(entry)
    )

    return entry
