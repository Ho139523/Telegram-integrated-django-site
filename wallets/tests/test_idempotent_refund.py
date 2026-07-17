# wallets/tests/test_idempotent_refund.py

from decimal import Decimal
from uuid import uuid4

from django.test import TestCase

from accounts.models import ProfileModel

from wallets.models import Currency

from wallets.services import refund


class IdempotentRefundTests(TestCase):

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

    def test_duplicate_refund_is_ignored(self):

        operation_id = uuid4()

        refund(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("25"),
            operation_id=operation_id,
        )

        refund(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("25"),
            operation_id=operation_id,
        )

        balance = self.wallet.balances.get(
            currency=self.currency
        )

        self.assertEqual(
            balance.available,
            Decimal("25"),
        )
