from .base import BasePolicy

from wallets.exceptions import (
    SameWalletTransfer,
)


class TransferPolicy(BasePolicy):

    @classmethod
    def validate(cls, command):

        cls.validate_positive(
            command.amount
        )

        if (
            command.from_wallet.pk
            ==
            command.to_wallet.pk
        ):
            raise SameWalletTransfer()
