# wallets/tests/test_withdrawal_provider.py

from unittest.mock import AsyncMock, patch

from wallets.providers.base import WithdrawalResult


@patch(
    "wallets.tasks.process_withdrawal."
    "WithdrawalProviderFactory.get"
)
def test_provider_completed(
    self,
    mock_factory,
):

    provider = AsyncMock()

    provider.transfer.return_value = (
        WithdrawalResult(
            status="completed",
            external_reference="EXT-1",
        )
    )

    mock_factory.return_value = provider

    withdrawal = self.create_withdrawal()

    result = process_withdrawal(
        withdrawal.pk
    )

    withdrawal.refresh_from_db()
    self.balance.refresh_from_db()

    self.assertEqual(
        withdrawal.status,
        Withdrawal.Status.COMPLETED,
    )

    self.assertEqual(
        self.balance.locked,
        Decimal("0"),
    )
