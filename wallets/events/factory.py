# wallets/events/factory.py

from wallets.events.types import (
    DepositCreated,
    WithdrawalCreated,
    WithdrawalCompleted,
    WithdrawalFailed,
    TransferCompleted,
    RefundCreated,
    HoldCreated,
    HoldReleased,
    SalePendingCreated,
    SaleReleased,
    SaleRefunded,
)


class EventFactory:

    # ----------------------------------------------------
    # WalletEntry Events
    # ----------------------------------------------------

    @staticmethod
    def deposit(entry):

        return DepositCreated(
            wallet_id=entry.wallet_id,
            currency_id=entry.currency_id,
            amount=entry.amount,
            operation_id=entry.operation_id,
            reference_id=entry.reference_id,
        )

    @staticmethod
    def refund(entry):

        return RefundCreated(
            wallet_id=entry.wallet_id,
            currency_id=entry.currency_id,
            amount=entry.amount,
            operation_id=entry.operation_id,
        )

    @staticmethod
    def hold(entry):

        return HoldCreated(
            wallet_id=entry.wallet_id,
            currency_id=entry.currency_id,
            amount=entry.amount,
            operation_id=entry.operation_id,
        )

    @staticmethod
    def release(
        entry,
        *,
        to_pending: bool,
    ):

        return HoldReleased(
            wallet_id=entry.wallet_id,
            currency_id=entry.currency_id,
            amount=entry.amount,
            to_pending=to_pending,
            operation_id=entry.operation_id,
        )

    @staticmethod
    def sale_pending(entry):

        return SalePendingCreated(
            seller_wallet_id=entry.wallet_id,
            currency_id=entry.currency_id,
            amount=entry.amount,
            operation_id=entry.operation_id,
        )

    @staticmethod
    def sale_release(
        entry,
        *,
        commission,
    ):

        return SaleReleased(
            seller_wallet_id=entry.wallet_id,
            currency_id=entry.currency_id,
            amount=entry.amount,
            commission=commission,
            operation_id=entry.operation_id,
        )

    @staticmethod
    def sale_refund(
        *,
        seller_entry,
        buyer_entry,
    ):

        return SaleRefunded(
            seller_wallet_id=seller_entry.wallet_id,
            buyer_wallet_id=buyer_entry.wallet_id,
            currency_id=seller_entry.currency_id,
            amount=abs(seller_entry.amount),
            operation_id=buyer_entry.operation_id,
        )

    # ----------------------------------------------------
    # Withdrawal Events
    # ----------------------------------------------------

    @staticmethod
    def withdraw(withdrawal):

        return WithdrawalCreated(
            withdrawal_id=withdrawal.pk,
            wallet_id=withdrawal.wallet_id,
            currency_id=withdrawal.currency_id,
            amount=withdrawal.amount,
            fee=withdrawal.fee,
            operation_id=withdrawal.operation_id,
        )

    # ----------------------------------------------------
    # Transfer Events
    # ----------------------------------------------------

    @staticmethod
    def transfer(
        *,
        sender_entry,
        receiver_entry,
    ):

        return TransferCompleted(
            from_wallet_id=sender_entry.wallet_id,
            to_wallet_id=receiver_entry.wallet_id,
            currency_id=sender_entry.currency_id,
            amount=receiver_entry.amount,
            operation_id=receiver_entry.operation_id,
        )


    @staticmethod
    def withdrawal_completed(withdrawal):

        return WithdrawalCompleted(
            withdrawal_id=withdrawal.pk,
            external_reference=withdrawal.external_reference,
        )


    @staticmethod
    def withdrawal_failed(withdrawal):

        return WithdrawalFailed(
            withdrawal_id=withdrawal.pk,
        )
