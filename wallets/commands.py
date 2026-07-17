# wallets/commands.py

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class DepositCommand:

    wallet: object
    currency: object

    amount: Decimal

    description: str = ""

    reference_id: UUID | None = None
    operation_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class WithdrawCommand:

    wallet: object
    currency: object

    amount: Decimal

    provider: str
    destination: str

    fee: Decimal = Decimal("0")

    operation_id: UUID | None = None



@dataclass(frozen=True, slots=True)
class TransferCommand:

    from_wallet: object
    to_wallet: object

    currency: object

    amount: Decimal

    description: str = ""

    reference_id: UUID | None = None

    operation_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class RefundCommand:

    wallet: object
    currency: object

    amount: Decimal

    description: str = ""

    reference_id: UUID | None = None

    operation_id: UUID | None = None



@dataclass(frozen=True, slots=True)
class HoldCommand:

    wallet: object
    currency: object

    amount: Decimal

    description: str = ""

    reference_id: UUID | None = None

    operation_id: UUID | None = None



@dataclass(frozen=True, slots=True)
class ReleaseCommand:

    wallet: object
    currency: object

    amount: Decimal

    to_pending: bool = False

    description: str = ""

    reference_id: UUID | None = None

    operation_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class SalePendingCommand:

    seller_wallet: object

    currency: object

    amount: Decimal

    reference_id: UUID | None = None

    operation_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class SaleReleaseCommand:

    seller_wallet: object

    currency: object

    amount: Decimal

    commission: Decimal

    reference_id: UUID | None = None

    operation_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class SaleRefundCommand:

    seller_wallet: object

    buyer_wallet: object

    currency: object

    amount: Decimal

    reference_id: UUID | None = None

    operation_id: UUID | None = None



