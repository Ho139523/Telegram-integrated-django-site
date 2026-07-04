# wallets/tests/test_deposit.py

from decimal import Decimal

from django.test import TestCase

from accounts.models import ProfileModel
from wallets.models import Currency
from wallets.services import deposit




class DepositTests(TestCase):

    def setUp(self):

        self.wallet = ProfileModel.objects.create(
            tel_id="10001",
            fname="Seller",
        ).wallet

        self.currency = Currency.objects.create(
            code="USD",
            name="US Dollar",
            symbol="$",
        )

    def test_deposit_increases_balance(self):

        deposit(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("100"),
        )

        balance = self.wallet.balances.get(
            currency=self.currency
        )

        self.assertEqual(
            balance.available,
            Decimal("100")
        )

    def test_negative_deposit_raises_error(self):

        with self.assertRaises(ValueError):

            deposit(
                wallet=self.wallet,
                currency=self.currency,
                amount=Decimal("-10"),
            )
