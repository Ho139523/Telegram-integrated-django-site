# wallets/services/conversion.py

from decimal import Decimal

from wallets.services.decorators import idempotent
from wallets.models import ExchangeRate


def convert(
    *,
    amount: Decimal,
    from_currency,
    to_currency,
):

    if from_currency == to_currency:
        return amount

    rate = ExchangeRate.objects.get(
        from_currency=from_currency,
        to_currency=to_currency,
    )

    return amount * rate.rate
