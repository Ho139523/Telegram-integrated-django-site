from django.db import transaction
from wallets.events.publisher import EventPublisher

from wallets.constants import Services
from wallets.models import WalletEntry

from wallets.repositories import (
    BalanceRepository,
    EntryRepository,
)

from wallets.services.base import (
    validate_positive,
    ensure_balance,
)

from wallets.services.decorators import idempotent

from wallets.events.factory import EventFactory


@transaction.atomic
@idempotent(Services.HOLD)
def hold(
    *,
    wallet,
    currency,
    amount,
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
        "available",
        amount,
    )

    balance.available -= amount
    balance.locked += amount

    BalanceRepository.save(
        balance,
        fields=[
            "available",
            "locked",
        ],
    )

    
    entry = EntryRepository.create(
        wallet=wallet,
        currency=currency,
        amount=amount,
        entry_type=WalletEntry.Type.HOLD,
        description=description,
        reference_id=reference_id,
        operation_id=operation_id,
    )

    EventPublisher.publish(
            EventFactory.hold(entry)
    )

    return entry


