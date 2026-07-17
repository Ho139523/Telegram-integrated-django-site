from decimal import Decimal
from uuid import uuid4

from django.test import TestCase

from accounts.models import ProfileModel

from wallets.models import Currency

from wallets.services import (
    deposit,
    transfer,
)


class IdempotentTransferTests(TestCase):

    def setUp(self):

        self.currency = Currency.objects.create(
            code="USD",
            name="US Dollar",
            symbol="$",
        )

        self.wallet1 = ProfileModel.objects.create(
            tel_id="10001",
            fname="Seller",
        ).wallet

        self.wallet2 = ProfileModel.objects.create(
            tel_id="10002",
            fname="Buyer",
        ).wallet

    def test_duplicate_transfer_is_ignored(self):

        deposit(
            wallet=self.wallet1,
            currency=self.currency,
            amount=Decimal("100"),
        )

        operation_id = uuid4()

        transfer(
            from_wallet=self.wallet1,
            to_wallet=self.wallet2,
            currency=self.currency,
            amount=Decimal("30"),
            operation_id=operation_id,
        )

        transfer(
            from_wallet=self.wallet1,
            to_wallet=self.wallet2,
            currency=self.currency,
            amount=Decimal("30"),
            operation_id=operation_id,
        )

        sender = self.wallet1.balances.get(
            currency=self.currency
        )

        receiver = self.wallet2.balances.get(
            currency=self.currency
        )

        self.assertEqual(
            sender.available,
            Decimal("70"),
        )

        self.assertEqual(
            receiver.available,
            Decimal("30"),
        )
