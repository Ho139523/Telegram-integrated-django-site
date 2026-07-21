# wallets/tests/test_complete_vs_fail_race.py

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
    fail_withdrawal,
)


class WithdrawalRaceTests(TransactionTestCase):

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

    def complete_worker(
        self,
        results,
        errors,
    ):

        close_old_connections()

        try:

            withdrawal = Withdrawal.objects.get(
                pk=self.withdrawal.pk,
            )

            complete_withdrawal(
                withdrawal,
                external_reference="BANK-001",
            )

            results.append("completed")

        except Exception as exc:

            errors.append(type(exc).__name__)

        finally:

            close_old_connections()

    def fail_worker(
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

            results.append("failed")

        except Exception as exc:

            errors.append(type(exc).__name__)

        finally:

            close_old_connections()

    def test_complete_vs_fail_race(self):

        results = []
        errors = []

        t1 = Thread(
            target=self.complete_worker,
            args=(results, errors),
        )

        t2 = Thread(
            target=self.fail_worker,
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

        #
        # وضعیت نهایی فقط یکی از این دو باشد.
        #
        self.assertIn(
            self.withdrawal.status,
            [
                Withdrawal.Status.COMPLETED,
                Withdrawal.Status.FAILED,
            ],
        )

        #
        # locked همیشه صفر شود.
        #
        self.assertEqual(
            balance.locked,
            Decimal("0"),
        )

        #
        # اگر Complete برنده شد.
        #
        if self.withdrawal.status == Withdrawal.Status.COMPLETED:

            self.assertEqual(
                balance.available,
                Decimal("20"),
            )

            self.assertEqual(
                self.withdrawal.external_reference,
                "BANK-001",
            )

        #
        # اگر Fail برنده شد.
        #
        else:

            self.assertEqual(
                balance.available,
                Decimal("100"),
            )
