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
    complete_withdrawal,
)


class WithdrawalCompleteTests(TestCase):

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

    def test_complete_withdrawal(self):

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

        complete_withdrawal(
            withdrawal,
            external_reference="BANK-001",
        )

        balance = self.wallet.balances.get(
            currency=self.currency,
        )

        self.assertEqual(
            balance.available,
            Decimal("60"),
        )

        self.assertEqual(
            balance.locked,
            Decimal("0"),
        )

        withdrawal.refresh_from_db()

        self.assertEqual(
            withdrawal.status,
            Withdrawal.Status.COMPLETED,
        )

        self.assertEqual(
            withdrawal.external_reference,
            "BANK-001",
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
        # WithdrawalCompleted
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
                "WithdrawalCompleted",
            ],
        )
