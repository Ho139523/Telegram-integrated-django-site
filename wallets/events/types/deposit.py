# events/types/deposit.py

from dataclasses import dataclass
from decimal import Decimal

from wallets.events.base import DomainEvent


@dataclass(
    slots=True,
    frozen=True,
)
class DepositCreated(DomainEvent):

    wallet_id: int

    currency_id: int

    amount: Decimal

    operation_id: str | None

    reference_id: str | None
