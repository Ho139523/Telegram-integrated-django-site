# wallets/validators.py

from wallets.exceptions import (
    InvalidAmount,
)


class BaseValidator:

    @classmethod
    def validate(cls, command):
        raise NotImplementedError



class DepositValidator(BaseValidator):

    @classmethod
    def validate(cls, command):

        if command.amount <= 0:
            raise InvalidAmount(
                "Deposit amount must be positive."
            )



class WithdrawValidator(BaseValidator):

    @classmethod
    def validate(cls, command):

        if command.amount <= 0:
            raise InvalidAmount(
                "Withdraw amount must be positive."
            )

        if command.fee < 0:
            raise InvalidAmount(
                "Fee cannot be negative."
            )



class TransferValidator(BaseValidator):

    @classmethod
    def validate(cls, command):

        if command.amount <= 0:
            raise InvalidAmount()

        if command.from_wallet == command.to_wallet:
            raise ValueError(
                "Cannot transfer to yourself."
            )



class RefundValidator(BaseValidator):

    @classmethod
    def validate(cls, command):

        if command.amount <= 0:
            raise InvalidAmount()



class HoldValidator(BaseValidator):

    @classmethod
    def validate(cls, command):

        if command.amount <= 0:
            raise InvalidAmount()



class ReleaseValidator(BaseValidator):

    @classmethod
    def validate(cls, command):

        if command.amount <= 0:
            raise InvalidAmount()



class SalePendingValidator(BaseValidator):

    @classmethod
    def validate(cls, command):

        if command.amount <= 0:
            raise InvalidAmount()



class SaleReleaseValidator(BaseValidator):

    @classmethod
    def validate(cls, command):

        if command.amount <= 0:
            raise InvalidAmount()

        if command.commission < 0:
            raise InvalidAmount()

        if command.commission > command.amount:
            raise InvalidAmount(
                "Commission exceeds amount."
            )


class SaleRefundValidator(BaseValidator):

    @classmethod
    def validate(cls, command):

        if command.amount <= 0:
            raise InvalidAmount()




