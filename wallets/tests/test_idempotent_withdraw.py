# wallets/tests/test_idempotent_withdraw.py

from decimal import Decimal
from uuid import uuid4

from django.test import TestCase

from accounts.models import ProfileModel

from wallets.models import Currency

from wallets.services import (
    deposit,
    withdraw,
)


class IdempotentWithdrawalTests(TestCase):

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

    def test_duplicate_withdraw_is_ignored(self):

        deposit(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("100"),
        )

        operation_id = uuid4()

        withdraw(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("40"),
            provider="bank",
            destination="123456",
            operation_id=operation_id,
        )

        withdraw(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("40"),
            provider="bank",
            destination="123456",
            operation_id=operation_id,
        )

        balance = self.wallet.balances.get(
            currency=self.currency
        )

        self.assertEqual(
            balance.available,
            Decimal("60"),
        )

        self.assertEqual(
            balance.locked,
            Decimal("40"),
        )
