# wallets/tests/test_concurrent_withdrawal_fail.py

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
    fail_withdrawal,
)


class ConcurrentWithdrawalFailTests(TransactionTestCase):

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

    def worker(
        self,
        results,
        errors,
    ):

        close_old_connections()

        try:

            withdrawal = Withdrawal.objects.get(
                pk=self.withdrawal.pk,
            )

            fail_withdrawal(
                withdrawal,
            )

            results.append(True)

        except Exception as exc:

            errors.append(repr(exc))

        finally:

            close_old_connections()

    def test_two_parallel_fail(self):

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
            Withdrawal.Status.FAILED,
        )

        #
        # مبلغ باید فقط یک بار آزاد شده باشد.
        #
        self.assertEqual(
            balance.available,
            Decimal("100"),
        )

        self.assertEqual(
            balance.locked,
            Decimal("0"),
        )
