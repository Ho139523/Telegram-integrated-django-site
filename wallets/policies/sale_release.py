from .base import BasePolicy

from wallets.exceptions import (
    InvalidCommission,
)


class SaleReleasePolicy(BasePolicy):

    @classmethod
    def validate(cls, command):

        cls.validate_positive(
            command.amount
        )

        if command.commission < 0:
            raise InvalidCommission()

        if command.commission > command.amount:
            raise InvalidCommission()
