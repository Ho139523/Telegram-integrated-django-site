# wallets/repositories/wallet.py

from wallets.models import Wallet


class WalletRepository:

    @staticmethod
    def get(
        pk,
    ):
        return Wallet.objects.get(
            pk=pk
        )

    @staticmethod
    def get_for_update(
        pk,
    ):
        return (
            Wallet.objects
            .select_for_update()
            .get(
                pk=pk
            )
        )
