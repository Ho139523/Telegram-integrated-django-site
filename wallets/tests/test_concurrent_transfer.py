# wallets/tests/test_concurrent_transfer.py

from decimal import Decimal
from threading import Thread

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


class ConcurrentTransferTests(TransactionTestCase):

    reset_sequences = True

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
            amount=Decimal("100"),
        )

    def test_two_parallel_transfers(self):

        successes = []
        failures = []

        def worker():

            try:

                transfer(
                    from_wallet=self.sender,
                    to_wallet=self.receiver,
                    currency=self.currency,
                    amount=Decimal("80"),
                )

                successes.append(True)

            except ValueError:

                failures.append(True)

        t1 = Thread(target=worker)
        t2 = Thread(target=worker)

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        sender_balance = self.sender.balances.get(
            currency=self.currency,
        )

        receiver_balance = self.receiver.balances.get(
            currency=self.currency,
        )

        #
        # فقط یکی باید موفق شود.
        #
        self.assertEqual(
            len(successes),
            1,
        )

        self.assertEqual(
            len(failures),
            1,
        )

        #
        # موجودی فرستنده
        #
        self.assertEqual(
            sender_balance.available,
            Decimal("20"),
        )

        #
        # موجودی گیرنده
        #
        self.assertEqual(
            receiver_balance.available,
            Decimal("80"),
        )

        #
        # Deposit + TransferOut + TransferIn
        #
        self.assertEqual(
            WalletEntry.objects.count(),
            3,
        )

        entries = list(
            WalletEntry.objects.order_by("id")
        )

        self.assertEqual(
            entries[0].type,
            WalletEntry.Type.DEPOSIT,
        )

        self.assertEqual(
            entries[1].type,
            WalletEntry.Type.TRANSFER_OUT,
        )

        self.assertEqual(
            entries[2].type,
            WalletEntry.Type.TRANSFER_IN,
        )
