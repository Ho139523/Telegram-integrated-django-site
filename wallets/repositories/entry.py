# wallets/repositories/entry.py

from wallets.models import WalletEntry


class EntryRepository:

    @staticmethod
    def create(
        *,
        wallet,
        currency,
        amount,
        entry_type,
        description="",
        reference_id=None,
        operation_id=None,
    ):

        return WalletEntry.objects.create(
            wallet=wallet,
            currency=currency,
            amount=amount,
            type=entry_type,
            description=description,
            reference_id=reference_id,
            operation_id=operation_id,
        )
