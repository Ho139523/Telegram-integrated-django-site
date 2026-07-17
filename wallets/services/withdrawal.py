# wallets/services/withdrawal.py

from decimal import Decimal
from wallets.events.publisher import EventPublisher

from django.db import transaction

from wallets.constants import Services

from wallets.models import (
    Withdrawal,
    WalletEntry,
)

from wallets.services.base import (
    get_balance,
    ensure_balance,
    log_entry,
)

from wallets.services.decorators import idempotent

from wallets.events.factory import EventFactory
from wallets.services.base import validate_positive


@transaction.atomic
@idempotent(Services.WITHDRAW)
def withdraw(
    *,
    wallet,
    currency,
    amount: Decimal,
    provider: str,
    destination: str,
    fee: Decimal = Decimal("0"),
    operation_id=None,
):
    
    validate_positive(amount)

    if fee < 0:
        raise ValueError("Fee cannot be negative.")

    total = amount + fee

    balance = get_balance(
        wallet=wallet,
        currency=currency,
    )

    ensure_balance(
        balance,
        "available",
        total,
    )

    balance.available -= total
    balance.locked += total

    balance.save(
        update_fields=[
            "available",
            "locked",
        ]
    )

    withdrawal = Withdrawal.objects.create(
        wallet=wallet,
        currency=currency,
        amount=amount,
        fee=fee,
        provider=provider,
        destination=destination,
        operation_id=operation_id,
    )

    entry = log_entry(
        wallet=wallet,
        currency=currency,
        amount=-total,
        entry_type=WalletEntry.Type.WITHDRAW,
        description=f"Withdrawal #{withdrawal.pk}",
        operation_id=operation_id,
    )

    EventPublisher.publish(
        EventFactory.withdraw(withdrawal)
    )

    return withdrawal
