from decimal import Decimal

from django.test import TestCase

from accounts.models import ProfileModel

from wallets.models import (
    WalletEntry,
    OutboxEvent,
    Withdrawal,
    Currency,
)

from wallets.services import (
    sale_pending,
    sale_release,
    withdraw,
    complete_withdrawal,
)

from wallets.services.treasury import (
    get_treasury_wallet,
)


class MarketplaceWalletFlowTests(TestCase):

    def setUp(self):

        self.currency = Currency.objects.create(
            code="USD",
            name="US Dollar",
            symbol="$",
        )

        self.buyer = (
            ProfileModel.objects.create(
                tel_id="20001",
                fname="Buyer",
            )
        )

        self.seller = (
            ProfileModel.objects.create(
                tel_id="10001",
                fname="Seller",
            )
        )

        self.buyer_wallet = self.buyer.wallet
        self.seller_wallet = self.seller.wallet


    def test_complete_marketplace_payment_flow(self):

        #
        # مرحله ۱:
        # پرداخت سفارش و انتقال مبلغ به pending فروشنده
        #

        sale_pending(
            seller_wallet=self.seller_wallet,
            currency=self.currency,
            amount=Decimal("100"),
        )


        seller_balance = (
            self.seller_wallet
            .balances
            .get(
                currency=self.currency,
            )
        )


        self.assertEqual(
            seller_balance.pending,
            Decimal("100"),
        )


        #
        # مرحله ۲:
        # تکمیل سفارش و آزادسازی مبلغ
        #

        sale_release(
            seller_wallet=self.seller_wallet,
            currency=self.currency,
            amount=Decimal("100"),
            commission=Decimal("5"),
        )


        seller_balance.refresh_from_db()


        self.assertEqual(
            seller_balance.pending,
            Decimal("0"),
        )

        self.assertEqual(
            seller_balance.available,
            Decimal("95"),
        )


        #
        # بررسی کمیسیون پلتفرم
        #

        treasury_balance = (
            get_treasury_wallet()
            .balances
            .get(
                currency=self.currency,
            )
        )


        self.assertEqual(
            treasury_balance.available,
            Decimal("5"),
        )


        #
        # مرحله ۳:
        # درخواست برداشت فروشنده
        #

        withdrawal = withdraw(
            wallet=self.seller_wallet,
            currency=self.currency,
            amount=Decimal("50"),
            provider="bank",
            destination="IR123456",
        )


        seller_balance.refresh_from_db()


        self.assertEqual(
            seller_balance.available,
            Decimal("45"),
        )

        self.assertEqual(
            seller_balance.locked,
            Decimal("50"),
        )


        #
        # مرحله ۴:
        # موفقیت برداشت
        #

        complete_withdrawal(
            withdrawal,
            external_reference="BANK-001",
        )


        seller_balance.refresh_from_db()


        self.assertEqual(
            seller_balance.available,
            Decimal("45"),
        )

        self.assertEqual(
            seller_balance.locked,
            Decimal("0"),
        )


        withdrawal.refresh_from_db()


        self.assertEqual(
            withdrawal.status,
            Withdrawal.Status.COMPLETED,
        )

        self.assertEqual(
            withdrawal.external_reference,
            "BANK-001",
        )


        self.assertIsNotNone(
            withdrawal.processed_at,
        )


        #
        # Ledger verification
        #
        # SALE_PENDING
        # SALE_RELEASE
        # COMMISSION
        # WITHDRAWAL
        #

        self.assertEqual(
            WalletEntry.objects.count(),
            4,
        )


        entries = list(
            WalletEntry.objects.order_by(
                "id"
            ).values_list(
                "type",
                flat=True,
            )
        )


        self.assertEqual(
            entries,
            [
                WalletEntry.Type.SALE_PENDING,
                WalletEntry.Type.SALE_RELEASE,
                WalletEntry.Type.COMMISSION,
                WalletEntry.Type.WITHDRAW,
            ],
        )


        #
        # Outbox verification
        #
        # SalePendingCreated
        # SaleReleased
        # WithdrawalCreated
        # WithdrawalCompleted
        #

        self.assertEqual(
            OutboxEvent.objects.count(),
            4,
        )


        events = list(
            OutboxEvent.objects.order_by(
                "id"
            ).values_list(
                "event_type",
                flat=True,
            )
        )


        self.assertEqual(
            events,
            [
                "SalePendingCreated",
                "SaleReleased",
                "WithdrawalCreated",
                "WithdrawalCompleted",
            ],
        )
