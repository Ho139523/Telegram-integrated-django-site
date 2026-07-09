# wallets/services/utils.py

from wallets.models import WalletEntry


def operation_exists(
    *,
    operation_id,
    entry_type,
):

    if operation_id is None:
        return False

    return WalletEntry.objects.filter(
        operation_id=operation_id,
        type=entry_type,
    ).exists()
