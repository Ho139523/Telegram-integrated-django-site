from django.db import transaction
from wallets.events.publisher import EventPublisher

from wallets.constants import Services
from wallets.models import WalletEntry

from wallets.repositories import (
    BalanceRepository,
    EntryRepository,
)

from wallets.services.base import validate_positive
from wallets.services.decorators import idempotent

from wallets.events.factory import EventFactory


@transaction.atomic
@idempotent(Services.REFUND)
def refund(
    *,
    wallet,
    currency,
    amount,
    description="",
    reference_id=None,
    operation_id=None,
):

    validate_positive(amount)

    balance, _ = BalanceRepository.get_or_create_for_update(
        wallet=wallet,
        currency=currency,
    )

    balance.available += amount

    BalanceRepository.save(
        balance,
        fields=["available"],
    )

    entry = EntryRepository.create(
        wallet=wallet,
        currency=currency,
        amount=amount,
        entry_type=WalletEntry.Type.REFUND,
        description=description,
        reference_id=reference_id,
        operation_id=operation_id,
    )

    EventPublisher.publish(
        EventFactory.refund(entry)
    )

    return entry
