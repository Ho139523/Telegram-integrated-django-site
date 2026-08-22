@patch(
    "wallets.tasks.process_withdrawal."
    "WithdrawalProviderFactory.get"
)
def test_provider_failed(
    self,
    mock_factory,
):

    provider = AsyncMock()

    provider.transfer.return_value = (
        WithdrawalResult(
            status="failed",
            message="Rejected",
        )
    )

    mock_factory.return_value = provider

    withdrawal = self.create_withdrawal()

    process_withdrawal(
        withdrawal.pk
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

