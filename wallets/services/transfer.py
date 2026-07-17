# wallets/services/transfer.py

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
@idempotent(Services.TRANSFER)
def transfer(
    *,
    from_wallet,
    to_wallet,
    currency,
    amount,
    description="",
    reference_id=None,
    operation_id=None,
):

    validate_positive(amount)

    if from_wallet == to_wallet:
        raise ValueError(
            "Cannot transfer to yourself."
        )

    sender = get_balance(
        wallet=from_wallet,
        currency=currency,
    )

    ensure_balance(
        sender,
        "available",
        amount,
    )

    receiver = get_balance(
        wallet=to_wallet,
        currency=currency,
        create=True,
    )

    sender.available -= amount
    receiver.available += amount

    sender.save(
        update_fields=[
            "available",
        ]
    )

    receiver.save(
        update_fields=[
            "available",
        ]
    )

    sender_entry = log_entry(
        wallet=from_wallet,
        currency=currency,
        amount=-amount,
        entry_type=WalletEntry.Type.TRANSFER_OUT,
        description=description,
        reference_id=reference_id,
        operation_id=operation_id,
    )

    receiver_entry = log_entry(
        wallet=to_wallet,
        currency=currency,
        amount=amount,
        entry_type=WalletEntry.Type.TRANSFER_IN,
        description=description,
        reference_id=reference_id,
        operation_id=operation_id,
    )

    EventPublisher.publish(
        EventFactory.transfer(
            sender_entry=sender_entry,
            receiver_entry=receiver_entry,
        )
    )

    return receiver_entry
