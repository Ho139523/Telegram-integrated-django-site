# events/types/sale_refund.py

from dataclasses import dataclass
from decimal import Decimal

from wallets.events.base import DomainEvent


@dataclass(
    slots=True,
    frozen=True,
)
class SaleRefunded(DomainEvent):

    seller_wallet_id: int

    buyer_wallet_id: int

    currency_id: int

    amount: Decimal

    operation_id: str | None
