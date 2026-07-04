# wallets/tests/test_hold.py

from decimal import Decimal

from django.test import TestCase

from accounts.models import ProfileModel
from wallets.models import Currency
from wallets.services import (
    deposit,
    hold,
)



class HoldTests(TestCase):

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

    def test_hold_balance(self):

        deposit(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("100"),
        )

        hold(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("40"),
        )

        balance = self.wallet.balances.get(
            currency=self.currency
        )

        self.assertEqual(
            balance.available,
            Decimal("60")
        )

        self.assertEqual(
            balance.locked,
            Decimal("40")
        )

    def test_hold_more_than_available(self):

        deposit(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("50"),
        )

        with self.assertRaises(ValueError):

            hold(
                wallet=self.wallet,
                currency=self.currency,
                amount=Decimal("100"),
            )
