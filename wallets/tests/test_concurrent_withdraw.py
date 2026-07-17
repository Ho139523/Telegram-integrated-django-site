import traceback
from decimal import Decimal
from threading import Thread

from django.test import TransactionTestCase

from accounts.models import ProfileModel

from wallets.models import Currency
from wallets.services import (
    deposit,
    withdraw,
)


class ConcurrentWithdrawTests(TransactionTestCase):

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

    def test_two_parallel_withdrawals(self):

        results = []
        errors = []

        def worker():

            try:

                withdraw(
                    wallet=self.wallet,
                    currency=self.currency,
                    amount=Decimal("80"),
                    provider="bank",
                    destination="IR123",
                )

                results.append(True)


            except Exception as e:
                traceback.print_exc()
                errors.append(repr(e))


        t1 = Thread(target=worker)
        t2 = Thread(target=worker)

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
            balance.locked,
            Decimal("80"),
        )

        print("results =", results)
        print("errors =", errors)
