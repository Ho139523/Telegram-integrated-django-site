# wallets/tests/test_stress_withdraw.py

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

from django.db import close_old_connections
from django.test import TransactionTestCase

from accounts.models import ProfileModel

from wallets.models import (
    Currency,
    WalletEntry,
    Withdrawal,
)

from wallets.services import (
    deposit,
    withdraw,
)


class StressWithdrawTests(TransactionTestCase):

    reset_sequences = True

    MAX_WORKERS = 20

    OPERATIONS = 100

    AMOUNT = Decimal("20")

    INITIAL_BALANCE = Decimal("1000")

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
            amount=self.INITIAL_BALANCE,
        )

    def worker(self):

        close_old_connections()

        try:

            withdraw(
                wallet=self.wallet,
                currency=self.currency,
                amount=self.AMOUNT,
                provider="bank",
                destination="IR123",
            )

            return True

        except Exception as exc:

            return exc

        finally:

            close_old_connections()

    def test_stress_withdraw(self):

        with ThreadPoolExecutor(
            max_workers=self.MAX_WORKERS,
        ) as executor:

            results = list(
                executor.map(
                    lambda _: self.worker(),
                    range(self.OPERATIONS),
                )
            )

        success = [
            r for r in results
            if r is True
        ]

        errors = [
            r for r in results
            if r is not True
        ]

        balance = self.wallet.balances.get(
            currency=self.currency,
        )

        expected_success = int(
            self.INITIAL_BALANCE / self.AMOUNT
        )

        expected_fail = (
            self.OPERATIONS - expected_success
        )

        #
        # تعداد برداشت‌های موفق
        #
        self.assertEqual(
            len(success),
            expected_success,
        )

        #
        # تعداد برداشت‌های ناموفق
        #
        self.assertEqual(
            len(errors),
            expected_fail,
        )

        #
        # موجودی نهایی
        #
        self.assertEqual(
            balance.available,
            Decimal("0"),
        )

        self.assertEqual(
            balance.locked,
            self.INITIAL_BALANCE,
        )

        #
        # تعداد رکوردهای Withdrawal
        #
        self.assertEqual(
            Withdrawal.objects.count(),
            expected_success,
        )

        #
        # تعداد Ledger Entry های برداشت
        #
        self.assertEqual(
            WalletEntry.objects.filter(
                type=WalletEntry.Type.WITHDRAW,
            ).count(),
            expected_success,
        )

        #
        # حفظ مجموع موجودی
        #
        self.assertEqual(
            balance.available + balance.locked,
            self.INITIAL_BALANCE,
        )

        #
        # هیچ موجودی منفی نباشد
        #
        self.assertGreaterEqual(
            balance.available,
            Decimal("0"),
        )

        self.assertGreaterEqual(
            balance.locked,
            Decimal("0"),
        )

        #
        # همه خطاها باید ناشی از کمبود موجودی باشند
        #
        for exc in errors:

            self.assertIsInstance(
                exc,
                ValueError,
            )

            self.assertEqual(
                str(exc),
                "Insufficient available balance.",
            )
