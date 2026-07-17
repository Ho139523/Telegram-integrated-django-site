# wallets/policies/base.py

from wallets.exceptions import InvalidAmount


class BasePolicy:

    @staticmethod
    def validate_positive(amount):

        if amount <= 0:
            raise InvalidAmount()
