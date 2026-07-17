# wallets/repositories/balance.py

from wallets.models import WalletBalance


class BalanceRepository:

    @staticmethod
    def get(
        *,
        wallet,
        currency,
    ):
        return WalletBalance.objects.get(
            wallet=wallet,
            currency=currency,
        )

    @staticmethod
    def get_for_update(
        *,
        wallet,
        currency,
    ):
        return (
            WalletBalance.objects
            .select_for_update()
            .get(
                wallet=wallet,
                currency=currency,
            )
        )

    @staticmethod
    def get_or_create(
        *,
        wallet,
        currency,
    ):
        return WalletBalance.objects.get_or_create(
            wallet=wallet,
            currency=currency,
        )

    @staticmethod
    def get_or_create_for_update(
        *,
        wallet,
        currency,
    ):
        return (
            WalletBalance.objects
            .select_for_update()
            .get_or_create(
                wallet=wallet,
                currency=currency,
            )
        )

    @staticmethod
    def save(
        balance,
        *,
        fields=None,
    ):
        if fields:
            balance.save(update_fields=fields)
        else:
            balance.save()

        return balance
