# wallets/tests/test_refund.py

from decimal import Decimal

from django.test import TestCase

from accounts.models import ProfileModel
from wallets.models import Currency
from wallets.services import refund




class RefundTests(TestCase):

    def setUp(self):

        self.currency = Currency.objects.create(
            code="USD",
            name="US Dollar",
            symbol="$",
        )

        self.wallet = ProfileModel.objects.create(
            tel_id="10001",
            fname="Seller",
        ).wallet

    def test_refund(self):

        refund(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("25"),
        )

        balance = self.wallet.balances.get(
            currency=self.currency
        )

        self.assertEqual(
            balance.available,
            Decimal("25")
        )
