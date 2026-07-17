# wallets/tests/test_transfer.py

from decimal import Decimal

from django.test import TestCase

from accounts.models import ProfileModel

from wallets.models import (
    Currency,
    WalletEntry,
    OutboxEvent,
)

from wallets.services import (
    deposit,
    transfer,
)


class TransferTests(TestCase):

    def setUp(self):

        self.currency = Currency.objects.create(
            code="USD",
            name="US Dollar",
            symbol="$",
        )

        self.wallet1 = ProfileModel.objects.create(
            tel_id="10001",
            fname="Seller",
        ).wallet

        self.wallet2 = ProfileModel.objects.create(
            tel_id="10002",
            fname="Buyer",
        ).wallet

    def test_transfer_money(self):

        deposit(
            wallet=self.wallet1,
            currency=self.currency,
            amount=Decimal("100"),
        )

        receiver_entry = transfer(
            from_wallet=self.wallet1,
            to_wallet=self.wallet2,
            currency=self.currency,
            amount=Decimal("30"),
        )

        sender = self.wallet1.balances.get(
            currency=self.currency
        )

        receiver = self.wallet2.balances.get(
            currency=self.currency
        )

        self.assertEqual(
            sender.available,
            Decimal("70"),
        )

        self.assertEqual(
            receiver.available,
            Decimal("30"),
        )

        self.assertEqual(
            sender.locked,
            Decimal("0"),
        )

        self.assertEqual(
            receiver.locked,
            Decimal("0"),
        )

        self.assertEqual(
            sender.pending,
            Decimal("0"),
        )

        self.assertEqual(
            receiver.pending,
            Decimal("0"),
        )

        #
        # Deposit + TransferOut + TransferIn
        #

        self.assertEqual(
            WalletEntry.objects.count(),
            3,
        )

        sender_entry = WalletEntry.objects.filter(
            wallet=self.wallet1,
            type=WalletEntry.Type.TRANSFER_OUT,
        ).first()

        self.assertIsNotNone(sender_entry)

        self.assertEqual(
            sender_entry.amount,
            Decimal("-30"),
        )

        self.assertEqual(
            receiver_entry.type,
            WalletEntry.Type.TRANSFER_IN,
        )

        self.assertEqual(
            receiver_entry.amount,
            Decimal("30"),
        )

        #
        # Deposit + Transfer
        #

        self.assertEqual(
            OutboxEvent.objects.count(),
            2,
        )

        event = OutboxEvent.objects.order_by("-id").first()

        self.assertEqual(
            event.event_type,
            "TransferCompleted",
        )

        self.assertFalse(
            event.published,
        )

    def test_cannot_transfer_more_than_available(self):

        deposit(
            wallet=self.wallet1,
            currency=self.currency,
            amount=Decimal("20"),
        )

        with self.assertRaises(ValueError):

            transfer(
                from_wallet=self.wallet1,
                to_wallet=self.wallet2,
                currency=self.currency,
                amount=Decimal("100"),
            )

        sender = self.wallet1.balances.get(
            currency=self.currency,
        )

        self.assertEqual(
            sender.available,
            Decimal("20"),
        )

        #
        # فقط Deposit
        #

        self.assertEqual(
            WalletEntry.objects.count(),
            1,
        )

        self.assertEqual(
            OutboxEvent.objects.count(),
            1,
        )

    def test_cannot_transfer_to_yourself(self):

        deposit(
            wallet=self.wallet1,
            currency=self.currency,
            amount=Decimal("100"),
        )

        with self.assertRaises(ValueError):

            transfer(
                from_wallet=self.wallet1,
                to_wallet=self.wallet1,
                currency=self.currency,
                amount=Decimal("20"),
            )

        balance = self.wallet1.balances.get(
            currency=self.currency,
        )

        self.assertEqual(
            balance.available,
            Decimal("100"),
        )

    def test_zero_transfer_raises_error(self):

        deposit(
            wallet=self.wallet1,
            currency=self.currency,
            amount=Decimal("100"),
        )

        with self.assertRaises(ValueError):

            transfer(
                from_wallet=self.wallet1,
                to_wallet=self.wallet2,
                currency=self.currency,
                amount=Decimal("0"),
            )

    def test_negative_transfer_raises_error(self):

        deposit(
            wallet=self.wallet1,
            currency=self.currency,
            amount=Decimal("100"),
        )

        with self.assertRaises(ValueError):

            transfer(
                from_wallet=self.wallet1,
                to_wallet=self.wallet2,
                currency=self.currency,
                amount=Decimal("-10"),
            )
