# wallets/services/base.py

from wallets.models import WalletBalance


def get_balance(
    *,
    wallet,
    currency,
    create=True,
    for_update=True,
):
    """
    دریافت موجودی کیف پول.

    create=True
        اگر وجود نداشت ایجاد می‌شود.

    for_update=True
        ردیف قفل می‌شود.
    """

    qs = WalletBalance.objects

    if for_update:
        qs = qs.select_for_update()

    if create:
        balance, _ = qs.get_or_create(
            wallet=wallet,
            currency=currency,
        )
        return balance

    return qs.get(
        wallet=wallet,
        currency=currency,
    )


from wallets.models import WalletEntry


def log_entry(
    *,
    wallet,
    currency,
    amount,
    entry_type,
    description="",
    reference_id=None,
    operation_id=None,
):

    return WalletEntry.objects.create(
        wallet=wallet,
        currency=currency,
        amount=amount,
        type=entry_type,
        description=description,
        reference_id=reference_id,
        operation_id=operation_id,
    )


from decimal import Decimal


def validate_positive(amount: Decimal):

    if amount <= 0:
        raise ValueError(
            "Amount must be positive."
        )



def ensure_balance(
    balance,
    field,
    amount,
):
    """
    بررسی کافی بودن موجودی.

    field:
        available
        locked
        pending
    """

    if getattr(balance, field) < amount:
        raise ValueError(
            f"Insufficient {field} balance."
        )
