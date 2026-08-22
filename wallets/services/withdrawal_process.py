# wallets/services/withdrawal_process.py

from django.db import transaction

from wallets.models import Withdrawal


@transaction.atomic
def start_withdrawal_processing(
    withdrawal_id,
):
    """
    Atomically claim a pending withdrawal.

    Only one worker can move a withdrawal from
    PENDING to PROCESSING.

    Returns:
        Withdrawal instance if successfully claimed.
        None otherwise.
    """

    withdrawal = (
        Withdrawal.objects
        .select_for_update()
        .get(
            pk=withdrawal_id
        )
    )

    if withdrawal.status != (
        Withdrawal.Status.PENDING
    ):
        return None

    withdrawal.status = (
        Withdrawal.Status.PROCESSING
    )

    withdrawal.save(
        update_fields=[
            "status",
        ]
    )

    return withdrawal
