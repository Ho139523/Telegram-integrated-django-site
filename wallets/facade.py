# wallets/facade.py

from wallets.commands import (
    DepositCommand,
    WithdrawCommand,
    TransferCommand,
    RefundCommand,
    HoldCommand,
    ReleaseCommand,
    SalePendingCommand,
    SaleReleaseCommand,
    SaleRefundCommand,
)

from wallets.policies import (
    DepositPolicy,
    WithdrawPolicy,
    TransferPolicy,
    RefundPolicy,
    HoldPolicy,
    ReleasePolicy,
    SalePendingPolicy,
    SaleReleasePolicy,
    SaleRefundPolicy,
)

from wallets.services import (
    deposit,
    withdraw,
    transfer,
    refund,
    hold,
    release,
    sale_pending,
    sale_release,
    sale_refund,
    complete_withdrawal,
    fail_withdrawal,
)


class WalletFacade:

    # =====================================================
    # Basic Operations
    # =====================================================

    @staticmethod
    def deposit(command: DepositCommand):

        DepositPolicy.validate(command)

        return deposit(
            wallet=command.wallet,
            currency=command.currency,
            amount=command.amount,
            description=command.description,
            reference_id=command.reference_id,
            operation_id=command.operation_id,
        )

    @staticmethod
    def withdraw(command: WithdrawCommand):

        WithdrawPolicy.validate(command)

        return withdraw(
            wallet=command.wallet,
            currency=command.currency,
            amount=command.amount,
            provider=command.provider,
            destination=command.destination,
            fee=command.fee,
            operation_id=command.operation_id,
        )

    @staticmethod
    def transfer(command: TransferCommand):

        TransferPolicy.validate(command)

        return transfer(
            from_wallet=command.from_wallet,
            to_wallet=command.to_wallet,
            currency=command.currency,
            amount=command.amount,
            description=command.description,
            reference_id=command.reference_id,
            operation_id=command.operation_id,
        )

    @staticmethod
    def refund(command: RefundCommand):

        RefundPolicy.validate(command)

        return refund(
            wallet=command.wallet,
            currency=command.currency,
            amount=command.amount,
            description=command.description,
            reference_id=command.reference_id,
            operation_id=command.operation_id,
        )

    # =====================================================
    # Reservation
    # =====================================================

    @staticmethod
    def hold(command: HoldCommand):

        HoldPolicy.validate(command)

        return hold(
            wallet=command.wallet,
            currency=command.currency,
            amount=command.amount,
            description=command.description,
            reference_id=command.reference_id,
            operation_id=command.operation_id,
        )

    @staticmethod
    def release(command: ReleaseCommand):

        ReleasePolicy.validate(command)

        return release(
            wallet=command.wallet,
            currency=command.currency,
            amount=command.amount,
            to_pending=command.to_pending,
            description=command.description,
            reference_id=command.reference_id,
            operation_id=command.operation_id,
        )

    # =====================================================
    # Marketplace
    # =====================================================

    @staticmethod
    def sale_pending(command: SalePendingCommand):

        SalePendingPolicy.validate(command)

        return sale_pending(
            seller_wallet=command.seller_wallet,
            currency=command.currency,
            amount=command.amount,
            reference_id=command.reference_id,
            operation_id=command.operation_id,
        )

    @staticmethod
    def sale_release(command: SaleReleaseCommand):

        SaleReleasePolicy.validate(command)

        return sale_release(
            seller_wallet=command.seller_wallet,
            currency=command.currency,
            amount=command.amount,
            commission=command.commission,
            reference_id=command.reference_id,
            operation_id=command.operation_id,
        )

    @staticmethod
    def sale_refund(command: SaleRefundCommand):

        SaleRefundPolicy.validate(command)

        return sale_refund(
            seller_wallet=command.seller_wallet,
            buyer_wallet=command.buyer_wallet,
            currency=command.currency,
            amount=command.amount,
            reference_id=command.reference_id,
            operation_id=command.operation_id,
        )

    # =====================================================
    # Withdrawal Lifecycle
    # =====================================================

    @staticmethod
    def complete_withdrawal(
        withdrawal,
        external_reference=None,
    ):
        return complete_withdrawal(
            withdrawal=withdrawal,
            external_reference=external_reference,
        )

    @staticmethod
    def fail_withdrawal(
        withdrawal,
    ):
        return fail_withdrawal(
            withdrawal=withdrawal,
        )
