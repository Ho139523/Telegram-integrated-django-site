# wallets/repositories/exchange_rate.py

from wallets.models import ExchangeRate


class ExchangeRateRepository:

    @staticmethod
    def get(
        *,
        from_currency,
        to_currency,
    ):
        return ExchangeRate.objects.get(
            from_currency=from_currency,
            to_currency=to_currency,
        )
