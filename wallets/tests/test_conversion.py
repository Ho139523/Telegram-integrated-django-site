# wallets/tests/test_conversion.py

from decimal import Decimal

from django.test import TestCase

from wallets.models import (
    Currency,
    ExchangeRate,
)

from wallets.services import convert


class ConversionTests(TestCase):

    def setUp(self):

        self.usd = Currency.objects.create(
            code="USD",
            name="US Dollar",
            symbol="$",
        )

        self.rub = Currency.objects.create(
            code="RUB",
            name="Russian Ruble",
            symbol="₽",
        )

        ExchangeRate.objects.create(
            from_currency=self.usd,
            to_currency=self.rub,
            rate=Decimal("80"),
            source="test",
        )

    def test_convert_usd_to_rub(self):

        result = convert(
            amount=Decimal("10"),
            from_currency=self.usd,
            to_currency=self.rub,
        )

        self.assertEqual(
            result,
            Decimal("800")
        )

    def test_same_currency_returns_same_amount(self):

        result = convert(
            amount=Decimal("15"),
            from_currency=self.usd,
            to_currency=self.usd,
        )

        self.assertEqual(
            result,
            Decimal("15")
        )
