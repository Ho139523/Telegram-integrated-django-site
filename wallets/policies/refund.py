from .base import BasePolicy


class RefundPolicy(BasePolicy):

    @classmethod
    def validate(cls, command):

        cls.validate_positive(
            command.amount
        )
