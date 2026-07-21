# wallets/tests/test_concurrent_withdrawal_complete.py

from threading import Thread
from decimal import Decimal

from django.db import close_old_connections
from django.test import TransactionTestCase

from accounts.models import ProfileModel

from wallets.models import (
    Currency,
    Withdrawal,
)

from wallets.services import (
    deposit,
    withdraw,
    complete_withdrawal,
)


class ConcurrentWithdrawalCompleteTests(TransactionTestCase):

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

        self.withdrawal = withdraw(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("80"),
            provider="bank",
            destination="IR123",
        )

    def test_two_parallel_complete(self):

        results = []
        errors = []

        def worker():

            close_old_connections()

            try:

                w = Withdrawal.objects.get(
                    pk=self.withdrawal.pk,
                )

                complete_withdrawal(
                    w,
                    external_reference="BANK-001",
                )

                results.append(True)

            except Exception as e:

                errors.append(type(e).__name__)

            finally:

                close_old_connections()

        t1 = Thread(target=worker)
        t2 = Thread(target=worker)

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        self.withdrawal.refresh_from_db()

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
            self.withdrawal.status,
            Withdrawal.Status.COMPLETED,
        )

        self.assertEqual(
            self.withdrawal.external_reference,
            "BANK-001",
        )

        self.assertEqual(
            balance.available,
            Decimal("20"),
        )

        self.assertEqual(
            balance.locked,
            Decimal("0"),
        )
