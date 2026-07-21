# wallets/tests/test_stress_sale_release.py

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
    sale_pending,
    sale_release,
)


class StressSaleReleaseTests(TransactionTestCase):

    reset_sequences = True

    MAX_WORKERS = 20

    OPERATIONS = 100

    AMOUNT = Decimal("10")

    INITIAL_BALANCE = Decimal("1000")

    COMMISSION = Decimal("0")

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

        sale_pending(
            seller_wallet=self.wallet,
            currency=self.currency,
            amount=self.INITIAL_BALANCE,
        )

    def worker(self):

        close_old_connections()

        try:

            sale_release(
                seller_wallet=self.wallet,
                currency=self.currency,
                amount=self.AMOUNT,
                commission=self.COMMISSION,
            )

            return True

        except Exception as exc:

            return exc

        finally:

            close_old_connections()

    def test_stress_sale_release(self):

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

        self.assertEqual(
            len(success),
            expected_success,
        )

        self.assertEqual(
            len(errors),
            self.OPERATIONS - expected_success,
        )

        self.assertEqual(
            balance.pending,
            Decimal("0"),
        )

        self.assertEqual(
            balance.available,
            self.INITIAL_BALANCE,
        )

        self.assertEqual(
            WalletEntry.objects.filter(
                type=WalletEntry.Type.SALE_RELEASE,
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
                "Insufficient pending balance.",
            )
