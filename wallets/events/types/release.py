# events/types/release.py

from dataclasses import dataclass
from decimal import Decimal


@dataclass(slots=True, frozen=True)
class HoldReleased:

    wallet_id: int

    currency_id: int

    amount: Decimal

    to_pending: bool

    operation_id: str | None
