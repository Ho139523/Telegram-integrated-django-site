# events/types/hold.py

from dataclasses import dataclass
from decimal import Decimal

from wallets.events.base import DomainEvent


@dataclass(
    slots=True,
    frozen=True,
)
class HoldCreated(DomainEvent):

    wallet_id: int

    currency_id: int

    amount: Decimal

    operation_id: str | None


@dataclass(
    slots=True,
    frozen=True,
)
class HoldReleased(DomainEvent):

    wallet_id: int

    currency_id: int

    amount: Decimal

    to_pending: bool

    operation_id: str | None
