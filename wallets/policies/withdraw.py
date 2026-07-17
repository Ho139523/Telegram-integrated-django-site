from .base import BasePolicy

from wallets.exceptions import (
    InvalidAmount,
)


class WithdrawPolicy(BasePolicy):

    @classmethod
    def validate(cls, command):

        cls.validate_positive(
            command.amount
        )

        if command.fee < 0:
            raise InvalidAmount()
