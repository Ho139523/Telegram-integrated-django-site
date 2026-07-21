from decimal import Decimal
from threading import Thread

from django.db import close_old_connections
from django.test import TransactionTestCase

from accounts.models import ProfileModel

from wallets.models import Currency
from wallets.services import (
    deposit,
    sale_pending,
)


class ConcurrentSalePendingTests(TransactionTestCase):

    reset_sequences = True

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

        deposit(
            wallet=self.wallet,
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

            sale_pending(
                seller_wallet=self.wallet,
                currency=self.currency,
                amount=Decimal("80"),
            )

            results.append(True)

        except Exception as e:

            errors.append(type(e).__name__)

        finally:

            close_old_connections()

    def test_two_parallel_sale_pending(self):

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

        balance = self.wallet.balances.get(
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

        self.assertEqual(
            balance.available,
            Decimal("20"),
        )

        self.assertEqual(
            balance.pending,
            Decimal("80"),
        )
