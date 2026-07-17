# wallets/tests/test_sale_pending.py

from decimal import Decimal

from django.test import TestCase

from accounts.models import ProfileModel

from wallets.models import (
    Currency,
    WalletEntry,
    OutboxEvent,
)

from wallets.services import sale_pending


class SalePendingTests(TestCase):

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

    def test_sale_pending(self):

        entry = sale_pending(
            seller_wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("100"),
        )

        balance = self.wallet.balances.get(
            currency=self.currency,
        )

        self.assertEqual(
            balance.available,
            Decimal("0"),
        )

        self.assertEqual(
            balance.locked,
            Decimal("0"),
        )

        self.assertEqual(
            balance.pending,
            Decimal("100"),
        )

        self.assertEqual(
            entry.type,
            WalletEntry.Type.SALE_PENDING,
        )

        self.assertEqual(
            entry.amount,
            Decimal("100"),
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
            "SalePendingCreated",
        )

        self.assertFalse(
            event.published,
        )

    def test_negative_sale_pending_raises_error(self):

        with self.assertRaises(ValueError):

            sale_pending(
                seller_wallet=self.wallet,
                currency=self.currency,
                amount=Decimal("-1"),
            )

        self.assertEqual(
            WalletEntry.objects.count(),
            0,
        )

        self.assertEqual(
            OutboxEvent.objects.count(),
            0,
        )

    def test_zero_sale_pending_raises_error(self):

        with self.assertRaises(ValueError):

            sale_pending(
                seller_wallet=self.wallet,
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
