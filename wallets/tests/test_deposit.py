from decimal import Decimal

from django.test import TestCase

from accounts.models import ProfileModel

from wallets.models import (
    Currency,
    WalletEntry,
    OutboxEvent,
)

from wallets.services import deposit


class DepositTests(TestCase):

    def setUp(self):

        self.currency = Currency.objects.create(
            code="USD",
            name="US Dollar",
            symbol="$",
        )

        self.wallet = (
            ProfileModel.objects.create(
                tel_id="10001",
                fname="Seller",
            ).wallet
        )

    def test_deposit_increases_balance(self):

        entry = deposit(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("100.00"),
        )

        balance = self.wallet.balances.get(
            currency=self.currency,
        )

        self.assertEqual(
            balance.available,
            Decimal("100.00"),
        )

        self.assertEqual(
            balance.locked,
            Decimal("0"),
        )

        self.assertEqual(
            balance.pending,
            Decimal("0"),
        )

        self.assertEqual(
            WalletEntry.objects.count(),
            1,
        )

        self.assertEqual(
            entry.type,
            WalletEntry.Type.DEPOSIT,
        )

        self.assertEqual(
            entry.wallet,
            self.wallet,
        )

        self.assertEqual(
            entry.amount,
            Decimal("100.00"),
        )

        #
        # Outbox
        #

        self.assertEqual(
            OutboxEvent.objects.count(),
            1,
        )

        event = OutboxEvent.objects.first()

        self.assertEqual(
            event.event_type,
            "DepositCreated",
        )

        self.assertFalse(
            event.published,
        )

    def test_negative_deposit_raises_error(self):

        with self.assertRaises(ValueError):

            deposit(
                wallet=self.wallet,
                currency=self.currency,
                amount=Decimal("-10"),
            )

        self.assertEqual(
            WalletEntry.objects.count(),
            0,
        )

        self.assertEqual(
            OutboxEvent.objects.count(),
            0,
        )

    def test_zero_deposit_raises_error(self):

        with self.assertRaises(ValueError):

            deposit(
                wallet=self.wallet,
                currency=self.currency,
                amount=Decimal("0"),
            )

        self.assertEqual(
            WalletEntry.objects.count(),
            0,
        )

        self.assertEqual(
            OutboxEvent.objects.count(),
            0,
        )
