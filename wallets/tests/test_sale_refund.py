# wallets/tests/test_sale_refund.py

from decimal import Decimal

from django.test import TestCase

from accounts.models import ProfileModel

from wallets.models import (
    Currency,
    WalletEntry,
    OutboxEvent,
)

from wallets.services import (
    sale_pending,
    sale_refund,
)


class SaleRefundTests(TestCase):

    def setUp(self):

        self.currency = Currency.objects.create(
            code="USD",
            name="US Dollar",
            symbol="$",
        )

        self.seller_wallet = (
            ProfileModel.objects.create(
                tel_id="10001",
                fname="Seller",
            ).wallet
        )

        self.buyer_wallet = (
            ProfileModel.objects.create(
                tel_id="10002",
                fname="Buyer",
            ).wallet
        )

    def test_sale_refund(self):

        sale_pending(
            seller_wallet=self.seller_wallet,
            currency=self.currency,
            amount=Decimal("100"),
        )

        buyer_entry = sale_refund(
            seller_wallet=self.seller_wallet,
            buyer_wallet=self.buyer_wallet,
            currency=self.currency,
            amount=Decimal("100"),
        )

        seller = self.seller_wallet.balances.get(
            currency=self.currency,
        )

        buyer = self.buyer_wallet.balances.get(
            currency=self.currency,
        )

        self.assertEqual(
            seller.pending,
            Decimal("0"),
        )

        self.assertEqual(
            buyer.available,
            Decimal("100"),
        )

        self.assertEqual(
            buyer_entry.type,
            WalletEntry.Type.REFUND,
        )

        #
        # SALE_PENDING
        # SALE_REFUND
        # REFUND
        #
        self.assertEqual(
            WalletEntry.objects.count(),
            3,
        )

        #
        # sale_pending + sale_refund
        #
        self.assertEqual(
            OutboxEvent.objects.count(),
            2,
        )

        events = list(
            OutboxEvent.objects.order_by("id")
        )

        self.assertEqual(
            events[0].event_type,
            "SalePendingCreated",
        )

        self.assertEqual(
            events[1].event_type,
            "SaleRefunded",
        )

        self.assertFalse(
            events[0].published,
        )

        self.assertFalse(
            events[1].published,
        )

    def test_cannot_refund_more_than_pending(self):

        sale_pending(
            seller_wallet=self.seller_wallet,
            currency=self.currency,
            amount=Decimal("50"),
        )

        with self.assertRaises(ValueError):

            sale_refund(
                seller_wallet=self.seller_wallet,
                buyer_wallet=self.buyer_wallet,
                currency=self.currency,
                amount=Decimal("100"),
            )

        seller = self.seller_wallet.balances.get(
            currency=self.currency,
        )

        self.assertEqual(
            seller.pending,
            Decimal("50"),
        )

        #
        # فقط sale_pending انجام شده است.
        #
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

    def test_negative_amount_raises_error(self):

        with self.assertRaises(ValueError):

            sale_refund(
                seller_wallet=self.seller_wallet,
                buyer_wallet=self.buyer_wallet,
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

    def test_zero_amount_raises_error(self):

        with self.assertRaises(ValueError):

            sale_refund(
                seller_wallet=self.seller_wallet,
                buyer_wallet=self.buyer_wallet,
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
