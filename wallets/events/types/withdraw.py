# events/types/withdraw.py

from dataclasses import dataclass
from decimal import Decimal

from wallets.events.base import DomainEvent


@dataclass(
    slots=True,
    frozen=True,
)
class WithdrawalCreated(DomainEvent):

    withdrawal_id: int

    wallet_id: int

    currency_id: int

    amount: Decimal

    fee: Decimal

    operation_id: str | None


@dataclass(
    slots=True,
    frozen=True,
)
class WithdrawalCompleted(DomainEvent):

    withdrawal_id: int

    external_reference: str | None


@dataclass(
    slots=True,
    frozen=True,
)
class WithdrawalFailed(DomainEvent):

    withdrawal_id: int
