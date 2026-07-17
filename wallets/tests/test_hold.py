# wallets/tests/test_hold.py

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
    hold,
)


class HoldTests(TestCase):

    def setUp(self):

        self.currency = Currency.objects.create(
            code="USD",
            name="US Dollar",
            symbol="$",
        )

        self.wallet = ProfileModel.objects.create(
            tel_id="10001",
            fname="Seller",
        ).wallet

    def test_hold_balance(self):

        deposit(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("100"),
        )

        entry = hold(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("40"),
        )

        balance = self.wallet.balances.get(
            currency=self.currency
        )

        self.assertEqual(
            balance.available,
            Decimal("60")
        )

        self.assertEqual(
            balance.locked,
            Decimal("40")
        )

        self.assertEqual(
            balance.pending,
            Decimal("0")
        )

        self.assertEqual(
            entry.type,
            WalletEntry.Type.HOLD,
        )

        self.assertEqual(
            entry.amount,
            Decimal("40"),
        )

        #
        # Deposit + Hold
        #

        self.assertEqual(
            WalletEntry.objects.count(),
            2,
        )

        #
        # Deposit + Hold
        #

        self.assertEqual(
            OutboxEvent.objects.count(),
            2,
        )

        event = OutboxEvent.objects.order_by("-id").first()

        self.assertEqual(
            event.event_type,
            "HoldCreated",
        )

        self.assertFalse(
            event.published,
        )

    def test_hold_more_than_available(self):

        deposit(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("50"),
        )

        with self.assertRaises(ValueError):

            hold(
                wallet=self.wallet,
                currency=self.currency,
                amount=Decimal("100"),
            )

        balance = self.wallet.balances.get(
            currency=self.currency
        )

        self.assertEqual(
            balance.available,
            Decimal("50"),
        )

        self.assertEqual(
            balance.locked,
            Decimal("0"),
        )

        #
        # فقط Deposit باید ثبت شده باشد
        #

        self.assertEqual(
            WalletEntry.objects.count(),
            1,
        )

        self.assertEqual(
            OutboxEvent.objects.count(),
            1,
        )

    def test_zero_hold_raises_error(self):

        deposit(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("100"),
        )

        with self.assertRaises(ValueError):

            hold(
                wallet=self.wallet,
                currency=self.currency,
                amount=Decimal("0"),
            )

    def test_negative_hold_raises_error(self):

        deposit(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("100"),
        )

        with self.assertRaises(ValueError):

            hold(
                wallet=self.wallet,
                currency=self.currency,
                amount=Decimal("-10"),
            )
