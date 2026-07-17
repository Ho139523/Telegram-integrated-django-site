# wallets/tests/test_refund.py

from decimal import Decimal

from django.test import TestCase

from accounts.models import ProfileModel

from wallets.models import (
    Currency,
    WalletEntry,
    OutboxEvent,
)

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

        entry = refund(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("25"),
        )

        balance = self.wallet.balances.get(
            currency=self.currency
        )

        self.assertEqual(
            balance.available,
            Decimal("25"),
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
            entry.type,
            WalletEntry.Type.REFUND,
        )

        self.assertEqual(
            entry.amount,
            Decimal("25"),
        )

        self.assertEqual(
            WalletEntry.objects.count(),
            1,
        )

        self.assertEqual(
            OutboxEvent.objects.count(),
            1,
        )

        event = OutboxEvent.objects.first()

        self.assertEqual(
            event.event_type,
            "RefundCreated",
        )

        self.assertFalse(
            event.published,
        )

    def test_negative_refund_raises_error(self):

        with self.assertRaises(ValueError):

            refund(
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

    def test_zero_refund_raises_error(self):

        with self.assertRaises(ValueError):

            refund(
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
