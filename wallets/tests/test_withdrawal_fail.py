from decimal import Decimal

from django.test import TestCase

from accounts.models import ProfileModel

from wallets.models import (
    Currency,
    WalletEntry,
    OutboxEvent,
    Withdrawal,
)

from wallets.services import (
    deposit,
    withdraw,
    fail_withdrawal,
)


class WithdrawalFailTests(TestCase):

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

    def test_fail_withdrawal(self):

        deposit(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("100"),
        )

        withdrawal = withdraw(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("40"),
            provider="bank",
            destination="IR123",
        )

        fail_withdrawal(
            withdrawal,
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


        withdrawal.refresh_from_db()

        self.assertEqual(
            withdrawal.status,
            Withdrawal.Status.FAILED,
        )

        self.assertIsNotNone(
            withdrawal.processed_at,
        )


        #
        # deposit + withdraw
        #
        self.assertEqual(
            WalletEntry.objects.count(),
            2,
        )


        #
        # DepositCreated
        # WithdrawalCreated
        # WithdrawalFailed
        #
        self.assertEqual(
            OutboxEvent.objects.count(),
            3,
        )

        events = list(
            OutboxEvent.objects.order_by(
                "id"
            ).values_list(
                "event_type",
                flat=True,
            )
        )

        self.assertEqual(
            events,
            [
                "DepositCreated",
                "WithdrawalCreated",
                "WithdrawalFailed",
            ],
        )
