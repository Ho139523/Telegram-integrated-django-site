# wallets/tests/test_stress_transfer.py

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

from django.db import close_old_connections
from django.test import TransactionTestCase

from accounts.models import ProfileModel

from wallets.models import (
    Currency,
    WalletEntry,
)

from wallets.services import (
    deposit,
    transfer,
)


class StressTransferTests(TransactionTestCase):

    reset_sequences = True

    MAX_WORKERS = 20

    OPERATIONS = 100

    AMOUNT = Decimal("10")

    INITIAL_BALANCE = Decimal("1000")

    def setUp(self):

        self.currency = Currency.objects.create(
            code="USD",
            name="US Dollar",
            symbol="$",
        )

        self.sender = (
            ProfileModel.objects.create(
                tel_id="10001",
                fname="Sender",
            ).wallet
        )

        self.receiver = (
            ProfileModel.objects.create(
                tel_id="10002",
                fname="Receiver",
            ).wallet
        )

        deposit(
            wallet=self.sender,
            currency=self.currency,
            amount=self.INITIAL_BALANCE,
        )

    def worker(self):

        close_old_connections()

        try:

            transfer(
                from_wallet=self.sender,
                to_wallet=self.receiver,
                currency=self.currency,
                amount=self.AMOUNT,
            )

            return True

        except Exception as exc:

            return exc

        finally:

            close_old_connections()

    def test_stress_transfer(self):

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

        sender = self.sender.balances.get(
            currency=self.currency,
        )

        receiver = self.receiver.balances.get(
            currency=self.currency,
        )

        expected_success = int(
            self.INITIAL_BALANCE / self.AMOUNT
        )

        self.assertEqual(
            len(success),
            expected_success,
        )

        self.assertEqual(
            len(errors),
            self.OPERATIONS - expected_success,
        )

        self.assertEqual(
            sender.available,
            Decimal("0"),
        )

        self.assertEqual(
            receiver.available,
            self.INITIAL_BALANCE,
        )

        #
        # مجموع دارایی سیستم باید حفظ شود.
        #
        self.assertEqual(
            sender.available +
            receiver.available,
            self.INITIAL_BALANCE,
        )

        #
        # دو Ledger Entry برای هر انتقال
        #
        self.assertEqual(
            WalletEntry.objects.filter(
                type=WalletEntry.Type.TRANSFER_OUT,
            ).count(),
            expected_success,
        )

        self.assertEqual(
            WalletEntry.objects.filter(
                type=WalletEntry.Type.TRANSFER_IN,
            ).count(),
            expected_success,
        )

        for exc in errors:

            self.assertIsInstance(
                exc,
                ValueError,
            )

            self.assertEqual(
                str(exc),
                "Insufficient available balance.",
            )
