from decimal import Decimal
from uuid import uuid4

from django.test import TestCase

from accounts.models import ProfileModel

from wallets.models import Currency

from wallets.services import deposit


class IdempotentDepositTests(TestCase):

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

    def test_duplicate_operation_is_ignored(self):

        operation_id = uuid4()

        deposit(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("100"),
            operation_id=operation_id,
        )

        deposit(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("100"),
            operation_id=operation_id,
        )

        balance = self.wallet.balances.get(
            currency=self.currency
        )

        self.assertEqual(
            balance.available,
            Decimal("100"),
        )
