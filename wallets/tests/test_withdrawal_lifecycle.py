from decimal import Decimal
from unittest.mock import AsyncMock, patch

from django.test import TestCase

from wallets.models import (
    WalletBalance,
    Withdrawal,
)

from wallets.services.withdrawal import withdraw
from wallets.services.withdrawal_process import (
    start_withdrawal_processing,
)
from wallets.services.withdrawal_complete import (
    complete_withdrawal,
)
from wallets.services.withdrawal_fail import (
    fail_withdrawal,
)


class WithdrawalLifecycleTests(TestCase):

    def setUp(self):

        self.wallet = ...
        self.currency = ...

        self.balance = WalletBalance.objects.create(
            wallet=self.wallet,
            currency=self.currency,
            available=Decimal("1000"),
            locked=Decimal("0"),
        )

    def create_withdrawal(self):

        return withdraw(
            wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("100"),
            provider="zarinpal",
            destination="TEST-DESTINATION",
            fee=Decimal("10"),
        )

    def test_withdraw_locks_balance(self):

        withdrawal = self.create_withdrawal()

        self.balance.refresh_from_db()

        self.assertEqual(
            withdrawal.status,
            Withdrawal.Status.PENDING,
        )

        self.assertEqual(
            self.balance.available,
            Decimal("890"),
        )

        self.assertEqual(
            self.balance.locked,
            Decimal("110"),
        )

    def test_pending_to_processing(self):

        withdrawal = self.create_withdrawal()

        result = start_withdrawal_processing(
            withdrawal.pk
        )

        self.assertEqual(
            result.status,
            Withdrawal.Status.PROCESSING,
        )

        withdrawal.refresh_from_db()

        self.assertEqual(
            withdrawal.status,
            Withdrawal.Status.PROCESSING,
        )

    def test_processing_to_completed(self):

        withdrawal = self.create_withdrawal()

        start_withdrawal_processing(
            withdrawal.pk
        )

        withdrawal.refresh_from_db()

        complete_withdrawal(
            withdrawal,
            external_reference="EXT-123",
        )

        withdrawal.refresh_from_db()
        self.balance.refresh_from_db()

        self.assertEqual(
            withdrawal.status,
            Withdrawal.Status.COMPLETED,
        )

        self.assertEqual(
            withdrawal.external_reference,
            "EXT-123",
        )

        self.assertEqual(
            self.balance.available,
            Decimal("890"),
        )

        self.assertEqual(
            self.balance.locked,
            Decimal("0"),
        )

    def test_processing_to_failed_returns_money(self):

        withdrawal = self.create_withdrawal()

        start_withdrawal_processing(
            withdrawal.pk
        )

        withdrawal.refresh_from_db()

        fail_withdrawal(
            withdrawal
        )

        withdrawal.refresh_from_db()
        self.balance.refresh_from_db()

        self.assertEqual(
            withdrawal.status,
            Withdrawal.Status.FAILED,
        )

        self.assertEqual(
            self.balance.available,
            Decimal("1000"),
        )

        self.assertEqual(
            self.balance.locked,
            Decimal("0"),
        )
