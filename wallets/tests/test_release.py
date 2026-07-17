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
    release,
)


class ReleaseTests(TestCase):

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

    def test_release_to_available(self):

        deposit(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("100"),
        )

        hold(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("40"),
        )

        entry = release(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("40"),
        )

        balance = self.wallet.balances.get(
            currency=self.currency,
        )

        self.assertEqual(
            balance.available,
            Decimal("100"),
        )

        self.assertEqual(
            balance.locked,
            Decimal("0"),
        )

        self.assertEqual(
            balance.pending,
            Decimal("0"),
        )

        self.assertEqual(
            entry.type,
            WalletEntry.Type.RELEASE,
        )

        self.assertEqual(
            entry.amount,
            Decimal("40"),
        )

    def test_release_to_pending(self):

        deposit(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("100"),
        )

        hold(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("50"),
        )

        release(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("50"),
            to_pending=True,
        )

        balance = self.wallet.balances.get(
            currency=self.currency,
        )

        self.assertEqual(
            balance.available,
            Decimal("50"),
        )

        self.assertEqual(
            balance.locked,
            Decimal("0"),
        )

        self.assertEqual(
            balance.pending,
            Decimal("50"),
        )

    def test_release_more_than_locked_raises_error(self):

        deposit(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("100"),
        )

        hold(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("20"),
        )

        with self.assertRaises(ValueError):

            release(
                wallet=self.wallet,
                currency=self.currency,
                amount=Decimal("30"),
            )

    def test_zero_amount_raises_error(self):

        deposit(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("100"),
        )

        hold(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("20"),
        )

        with self.assertRaises(ValueError):

            release(
                wallet=self.wallet,
                currency=self.currency,
                amount=Decimal("0"),
            )

    def test_negative_amount_raises_error(self):

        deposit(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("100"),
        )

        hold(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("20"),
        )

        with self.assertRaises(ValueError):

            release(
                wallet=self.wallet,
                currency=self.currency,
                amount=Decimal("-1"),
            )

    def test_wallet_entry_created(self):

        deposit(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("100"),
        )

        hold(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("25"),
        )

        release(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("25"),
        )

        entry = WalletEntry.objects.filter(
            type=WalletEntry.Type.RELEASE,
        ).first()

        self.assertIsNotNone(entry)

        self.assertEqual(
            entry.wallet,
            self.wallet,
        )

        self.assertEqual(
            entry.amount,
            Decimal("25"),
        )

    def test_outbox_event_created(self):

        deposit(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("100"),
        )

        hold(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("10"),
        )

        before = OutboxEvent.objects.count()

        release(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("10"),
        )

        self.assertEqual(
            OutboxEvent.objects.count(),
            before + 1,
        )

        event = OutboxEvent.objects.latest("id")

        self.assertEqual(
            event.event_type,
            "HoldReleased",
        )

        self.assertFalse(
            event.published,
        )
