from .base import BasePolicy


class SaleRefundPolicy(BasePolicy):

    @classmethod
    def validate(cls, command):

        cls.validate_positive(
            command.amount
        )
