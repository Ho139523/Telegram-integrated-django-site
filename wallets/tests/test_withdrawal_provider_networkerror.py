@patch(
    "wallets.tasks.process_withdrawal."
    "WithdrawalProviderFactory.get"
)
def test_provider_exception_keeps_withdrawal_processing(
    self,
    mock_factory,
):

    provider = AsyncMock()

    provider.transfer.side_effect = (
        TimeoutError(
            "Provider timeout"
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
        Withdrawal.Status.PROCESSING,
    )

    self.assertEqual(
        self.balance.available,
        Decimal("890"),
    )

    self.assertEqual(
        self.balance.locked,
        Decimal("110"),
    )

