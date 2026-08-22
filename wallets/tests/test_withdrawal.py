from decimal import Decimal

from django.test import TestCase

from accounts.models import ProfileModel
from wallets.models import Currency
from wallets.services import (
    deposit,
    withdraw,
    complete_withdrawal,
    fail_withdrawal,
)


class WithdrawalTests(TestCase):

    def setUp(self):

        self.currency = Currency.objects.create(
            code="USD",
            name="US Dollar",
            symbol="$",
        )

        self.profile = ProfileModel.objects.create(
            tel_id="10001",
            fname="Seller",
            preferred_currency=self.currency,
        )

        self.wallet = self.profile.wallet

    def test_complete_withdrawal(self):

        deposit(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("100"),
        )

        withdrawal = withdraw(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("40"),
            provider="bank",
            destination="123456",
        )

        complete_withdrawal(withdrawal)

        balance = self.wallet.balances.get(
            currency=self.currency
        )

        self.assertEqual(
            balance.available,
            Decimal("60"),
        )

        self.assertEqual(
            balance.locked,
            Decimal("0"),
        )

    def test_fail_withdrawal(self):

        deposit(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("100"),
        )

        withdrawal = withdraw(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("40"),
            provider="bank",
            destination="123456",
        )

        fail_withdrawal(withdrawal)

        balance = self.wallet.balances.get(
            currency=self.currency
        )

        self.assertEqual(
            balance.available,
            Decimal("100"),
        )

        self.assertEqual(
            balance.locked,
            Decimal("0"),
        )
