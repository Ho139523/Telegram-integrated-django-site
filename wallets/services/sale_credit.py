# wallets/services/sale_pending_from_payment.py

from decimal import Decimal

from django.db import transaction

from wallets.constants import Services
from wallets.events.factory import EventFactory
from wallets.events.publisher import EventPublisher
from wallets.models import WalletEntry
from wallets.services.base import (
    get_balance,
    log_entry,
    validate_positive,
)
from wallets.services.decorators import idempotent


@transaction.atomic
@idempotent(Services.SALE_CREDIT)
def sale_credit(
    *,
    seller_wallet,
    currency,
    amount,
    reference_id=None,
    operation_id=None,
):
    """
    ثبت درآمد حاصل از پرداخت مستقیم مشتری به درگاه.

    جریان مالی:

        Customer
            ↓
        Payment Gateway
            ↓
        Seller Revenue
            ↓
        WalletBalance.pending

    این سرویس از available چیزی کم نمی‌کند.

    pending:
        درآمد فروشنده‌ای که هنوز دوره مرجوعی آن تمام نشده است.

    available:
        موجودی قابل برداشت فروشنده که قبلاً آزاد شده است.
    """

    amount = Decimal(amount)

    validate_positive(amount)

    balance = get_balance(
        wallet=seller_wallet,
        currency=currency,
    )

    balance.pending += amount

    balance.save(
        update_fields=[
            "pending",
        ]
    )

    entry = log_entry(
        wallet=seller_wallet,
        currency=currency,
        amount=amount,
        entry_type=WalletEntry.Type.SALE_PENDING,
        reference_id=reference_id,
        operation_id=operation_id,
        description="Sale revenue credited from payment gateway",
    )

    EventPublisher.publish(
        EventFactory.sale_pending(entry)
    )

    return entry
