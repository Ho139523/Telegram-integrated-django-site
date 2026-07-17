from .base import BasePolicy


class ReleasePolicy(BasePolicy):

    @classmethod
    def validate(cls, command):

        cls.validate_positive(
            command.amount
        )
