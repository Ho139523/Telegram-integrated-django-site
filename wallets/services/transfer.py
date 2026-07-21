# wallets/services/transfer.py

from django.db import transaction

from wallets.constants import Services
from wallets.events.factory import EventFactory
from wallets.events.publisher import EventPublisher

from wallets.models import WalletEntry

from wallets.services.base import (
    get_balance,
    log_entry,
    ensure_balance,
    validate_positive,
)

from wallets.services.decorators import idempotent


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

    #
    # Always lock wallets in a deterministic order
    # to prevent deadlocks.
    #
    if from_wallet.id < to_wallet.id:
        first_wallet = from_wallet
        second_wallet = to_wallet
        sender_is_first = True
    else:
        first_wallet = to_wallet
        second_wallet = from_wallet
        sender_is_first = False

    first_balance = get_balance(
        wallet=first_wallet,
        currency=currency,
        create=not sender_is_first,
    )

    second_balance = get_balance(
        wallet=second_wallet,
        currency=currency,
        create=sender_is_first,
    )

    if sender_is_first:
        sender = first_balance
        receiver = second_balance
    else:
        sender = second_balance
        receiver = first_balance

    ensure_balance(
        sender,
        "available",
        amount,
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
