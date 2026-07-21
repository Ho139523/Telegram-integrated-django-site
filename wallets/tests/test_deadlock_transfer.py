# wallets/tests/test_deadlock_transfer.py

from decimal import Decimal
from threading import Thread

from django.test import TransactionTestCase

from accounts.models import ProfileModel

from wallets.services import (
    deposit,
    transfer,
)

from wallets.models import Currency


class DeadlockTransferTests(TransactionTestCase):

    reset_sequences = True

    def setUp(self):

        self.currency = Currency.objects.create(
            code="USD",
            name="Dollar",
            symbol="$",
        )

        self.wallet_a = (
            ProfileModel.objects.create(
                tel_id="10001",
                fname="A",
            ).wallet
        )

        self.wallet_b = (
            ProfileModel.objects.create(
                tel_id="10002",
                fname="B",
            ).wallet
        )

        deposit(
            wallet=self.wallet_a,
            currency=self.currency,
            amount=Decimal("100"),
        )

        deposit(
            wallet=self.wallet_b,
            currency=self.currency,
            amount=Decimal("100"),
        )

    def test_opposite_direction_transfer(self):

        errors = []

        def worker1():

            try:

                transfer(
                    from_wallet=self.wallet_a,
                    to_wallet=self.wallet_b,
                    currency=self.currency,
                    amount=Decimal("10"),
                )

            except Exception as e:

                errors.append(e)

        def worker2():

            try:

                transfer(
                    from_wallet=self.wallet_b,
                    to_wallet=self.wallet_a,
                    currency=self.currency,
                    amount=Decimal("20"),
                )

            except Exception as e:

                errors.append(e)

        t1 = Thread(target=worker1)
        t2 = Thread(target=worker2)

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        self.assertEqual(
            len(errors),
            0,
        )

        balance_a = self.wallet_a.balances.get(
            currency=self.currency,
        )

        balance_b = self.wallet_b.balances.get(
            currency=self.currency,
        )

        #
        # A:
        # 100 -10 +20 =110
        #
        self.assertEqual(
            balance_a.available,
            Decimal("110"),
        )

        #
        # B:
        #100 -20 +10 =90
        #
        self.assertEqual(
            balance_b.available,
            Decimal("90"),
        )
