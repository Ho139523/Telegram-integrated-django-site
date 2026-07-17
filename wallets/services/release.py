from django.db import transaction
from wallets.events.publisher import EventPublisher

from wallets.constants import Services
from wallets.models import WalletEntry

from wallets.repositories import (
    BalanceRepository,
    EntryRepository,
)

from wallets.services.base import ensure_balance
from wallets.services.decorators import idempotent

from wallets.events.factory import EventFactory

from wallets.services.base import (
    validate_positive,
    ensure_balance,
)


@transaction.atomic
@idempotent(Services.RELEASE)
def release(
    *,
    wallet,
    currency,
    amount,
    to_pending=False,
    description="",
    reference_id=None,
    operation_id=None,
):

    validate_positive(amount)
    
    balance = BalanceRepository.get_for_update(
        wallet=wallet,
        currency=currency,
    )

    ensure_balance(
        balance,
        "locked",
        amount,
    )

    balance.locked -= amount

    if to_pending:
        balance.pending += amount
        fields = [
            "locked",
            "pending",
        ]
    else:
        balance.available += amount
        fields = [
            "locked",
            "available",
        ]

    BalanceRepository.save(
        balance,
        fields=fields,
    )

    entry = EntryRepository.create(
        wallet=wallet,
        currency=currency,
        amount=amount,
        entry_type=WalletEntry.Type.RELEASE,
        description=description,
        reference_id=reference_id,
        operation_id=operation_id,
    )

    EventPublisher.publish(
        EventFactory.release(
            entry,
            to_pending=to_pending,
        )
    )

    return entry
