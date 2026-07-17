# wallets/tests/test_sale_release.py

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
    sale_release,
)

from wallets.services.treasury import (
    get_treasury_wallet,
)


class SaleReleaseTests(TestCase):

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

    def test_release_sale_funds(self):

        sale_pending(
            seller_wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("100"),
        )

        entry = sale_release(
            seller_wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("100"),
            commission=Decimal("5"),
        )

        seller = self.wallet.balances.get(
            currency=self.currency,
        )

        treasury = (
            get_treasury_wallet()
            .balances
            .get(currency=self.currency)
        )

        #
        # balances
        #

        self.assertEqual(
            seller.pending,
            Decimal("0"),
        )

        self.assertEqual(
            seller.available,
            Decimal("95"),
        )

        self.assertEqual(
            treasury.available,
            Decimal("5"),
        )

        #
        # returned entry
        #

        self.assertEqual(
            entry.type,
            WalletEntry.Type.SALE_RELEASE,
        )

        self.assertEqual(
            entry.amount,
            Decimal("100"),
        )

        #
        # ledger
        #

        self.assertEqual(
            WalletEntry.objects.filter(
                type=WalletEntry.Type.SALE_PENDING,
            ).count(),
            1,
        )

        self.assertEqual(
            WalletEntry.objects.filter(
                type=WalletEntry.Type.SALE_RELEASE,
            ).count(),
            1,
        )

        self.assertEqual(
            WalletEntry.objects.filter(
                type=WalletEntry.Type.COMMISSION,
            ).count(),
            1,
        )

        commission_entry = WalletEntry.objects.get(
            type=WalletEntry.Type.COMMISSION,
        )

        self.assertEqual(
            commission_entry.amount,
            Decimal("5"),
        )

        self.assertEqual(
            commission_entry.wallet,
            treasury.wallet,
        )

        #
        # outbox
        #

        self.assertEqual(
            OutboxEvent.objects.filter(
                event_type="SalePendingCreated",
            ).count(),
            1,
        )

        self.assertEqual(
            OutboxEvent.objects.filter(
                event_type="SaleReleased",
            ).count(),
            1,
        )

        sale_release_event = (
            OutboxEvent.objects.filter(
                event_type="SaleReleased",
            )
            .latest("id")
        )

        self.assertFalse(
            sale_release_event.published,
        )

    def test_commission_cannot_exceed_amount(self):

        sale_pending(
            seller_wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("100"),
        )

        with self.assertRaises(ValueError):

            sale_release(
                seller_wallet=self.wallet,
                currency=self.currency,
                amount=Decimal("100"),
                commission=Decimal("150"),
            )

        #
        # sale_pending event باید باقی مانده باشد
        #

        self.assertEqual(
            OutboxEvent.objects.filter(
                event_type="SalePendingCreated",
            ).count(),
            1,
        )

        self.assertFalse(
            OutboxEvent.objects.filter(
                event_type="SaleReleased",
            ).exists()
        )

    def test_negative_amount_raises_error(self):

        with self.assertRaises(ValueError):

            sale_release(
                seller_wallet=self.wallet,
                currency=self.currency,
                amount=Decimal("-1"),
                commission=Decimal("0"),
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

            sale_release(
                seller_wallet=self.wallet,
                currency=self.currency,
                amount=Decimal("0"),
                commission=Decimal("0"),
            )

        self.assertEqual(
            WalletEntry.objects.count(),
            0,
        )

        self.assertEqual(
            OutboxEvent.objects.count(),
            0,
        )

    def test_cannot_release_more_than_pending(self):

        sale_pending(
            seller_wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("50"),
        )

        with self.assertRaises(ValueError):

            sale_release(
                seller_wallet=self.wallet,
                currency=self.currency,
                amount=Decimal("100"),
                commission=Decimal("5"),
            )

        #
        # فقط SalePending ثبت شده باشد
        #

        self.assertEqual(
            WalletEntry.objects.filter(
                type=WalletEntry.Type.SALE_PENDING,
            ).count(),
            1,
        )

        self.assertEqual(
            WalletEntry.objects.filter(
                type=WalletEntry.Type.SALE_RELEASE,
            ).count(),
            0,
        )

        self.assertEqual(
            WalletEntry.objects.filter(
                type=WalletEntry.Type.COMMISSION,
            ).count(),
            0,
        )

        self.assertEqual(
            OutboxEvent.objects.filter(
                event_type="SalePendingCreated",
            ).count(),
            1,
        )

        self.assertFalse(
            OutboxEvent.objects.filter(
                event_type="SaleReleased",
            ).exists()
        )
