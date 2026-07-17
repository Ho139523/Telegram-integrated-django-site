# wallets/repositories/currency.py

from wallets.models import Currency


class CurrencyRepository:

    @staticmethod
    def get(
        code,
    ):
        return Currency.objects.get(
            code=code
        )
