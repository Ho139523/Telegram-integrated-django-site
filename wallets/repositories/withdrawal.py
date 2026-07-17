# wallets/repositories/withdrawal.py

from wallets.models import Withdrawal


class WithdrawalRepository:

    @staticmethod
    def create(
        **kwargs,
    ):
        return Withdrawal.objects.create(
            **kwargs
        )

    @staticmethod
    def get(
        pk,
    ):
        return Withdrawal.objects.get(
            pk=pk
        )

    @staticmethod
    def get_for_update(
        pk,
    ):
        return (
            Withdrawal.objects
            .select_for_update()
            .get(
                pk=pk
            )
        )

    @staticmethod
    def save(
        withdrawal,
        *,
        fields=None,
    ):

        if fields:
            withdrawal.save(
                update_fields=fields
            )
        else:
            withdrawal.save()

        return withdrawal
