# wallets/tests/test_concurrent_sale_refund.py

from decimal import Decimal
from threading import Thread

from django.db import close_old_connections
from django.test import TransactionTestCase

from accounts.models import ProfileModel

from wallets.models import (
    Currency,
    WalletEntry,
)

from wallets.services import (
    deposit,
    sale_pending,
    sale_refund,
)


class ConcurrentSaleRefundTests(TransactionTestCase):

    reset_sequences = True

    def setUp(self):

        self.currency = Currency.objects.create(
            code="USD",
            name="US Dollar",
            symbol="$",
        )

        self.seller = (
            ProfileModel.objects.create(
                tel_id="10001",
                fname="Seller",
            ).wallet
        )

        self.buyer = (
            ProfileModel.objects.create(
                tel_id="10002",
                fname="Buyer",
            ).wallet
        )

        deposit(
            wallet=self.seller,
            currency=self.currency,
            amount=Decimal("100"),
        )

        sale_pending(
            seller_wallet=self.seller,
            currency=self.currency,
            amount=Decimal("100"),
        )

    def worker(
        self,
        results,
        errors,
    ):

        close_old_connections()

        try:

            sale_refund(
                seller_wallet=self.seller,
                buyer_wallet=self.buyer,
                currency=self.currency,
                amount=Decimal("100"),
            )

            results.append(True)

        except Exception as exc:

            errors.append(repr(exc))

        finally:

            close_old_connections()

    def test_two_parallel_sale_refund(self):

        results = []
        errors = []

        t1 = Thread(
            target=self.worker,
            args=(results, errors),
        )

        t2 = Thread(
            target=self.worker,
            args=(results, errors),
        )

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        seller = self.seller.balances.get(
            currency=self.currency,
        )

        buyer = self.buyer.balances.get(
            currency=self.currency,
        )

        #
        # فقط یکی باید موفق شود.
        #
        self.assertEqual(
            len(results),
            1,
        )

        self.assertEqual(
            len(errors),
            1,
        )

        #
        # pending فقط یکبار آزاد شود.
        #
        self.assertEqual(
            seller.pending,
            Decimal("0"),
        )

        #
        # مبلغی به فروشنده برنمی‌گردد.
        #
        self.assertEqual(
            seller.available,
            Decimal("0"),
        )

        #
        # خریدار فقط یکبار پول بگیرد.
        #
        self.assertEqual(
            buyer.available,
            Decimal("100"),
        )

        #
        # Deposit + SalePending + SaleRefund + Refund
        #
        self.assertEqual(
            WalletEntry.objects.count(),
            4,
        )
