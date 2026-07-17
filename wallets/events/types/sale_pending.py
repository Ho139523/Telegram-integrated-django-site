# events/types/sale_pending.py

from dataclasses import dataclass
from decimal import Decimal

from wallets.events.base import DomainEvent


@dataclass(
    slots=True,
    frozen=True,
)
class SalePendingCreated(DomainEvent):

    seller_wallet_id: int

    currency_id: int

    amount: Decimal

    operation_id: str | None
