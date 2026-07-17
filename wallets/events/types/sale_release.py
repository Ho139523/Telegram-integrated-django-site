# events/types/sale_release.py

from dataclasses import dataclass
from decimal import Decimal

from wallets.events.base import DomainEvent


@dataclass(
    slots=True,
    frozen=True,
)
class SaleReleased(DomainEvent):

    seller_wallet_id: int

    currency_id: int

    amount: Decimal

    commission: Decimal

    operation_id: str | None
