# wallets/services/withdrawal_complete.py

from django.db import transaction
from django.utils import timezone

from wallets.events.publisher import EventPublisher

from wallets.models import (
    Withdrawal,
    WalletBalance,
)

from wallets.events.factory import EventFactory


@transaction.atomic
def complete_withdrawal(
    withdrawal: Withdrawal,
    external_reference: str | None = None,
):
    """
    Complete a withdrawal after the external provider
    has confirmed the transfer.

    Valid transition:

        PENDING -> COMPLETED
        PROCESSING -> COMPLETED

    The locked balance is released permanently because
    the money has been transferred externally.
    """

    withdrawal = (
        Withdrawal.objects
        .select_for_update()
        .get(pk=withdrawal.pk)
    )

    if withdrawal.status not in (
        Withdrawal.Status.PENDING,
        Withdrawal.Status.PROCESSING,
    ):
        raise ValueError(
            "Withdrawal cannot be completed "
            f"from status '{withdrawal.status}'."
        )

    balance = (
        WalletBalance.objects
        .select_for_update()
        .get(
            wallet=withdrawal.wallet,
            currency=withdrawal.currency,
        )
    )

    total = withdrawal.amount + withdrawal.fee

    if balance.locked < total:
        raise ValueError(
            "Insufficient locked balance."
        )

    balance.locked -= total

    balance.save(
        update_fields=[
            "locked",
        ]
    )

    withdrawal.status = Withdrawal.Status.COMPLETED
    withdrawal.processed_at = timezone.now()

    if external_reference:
        withdrawal.external_reference = (
            external_reference
        )

    withdrawal.save(
        update_fields=[
            "status",
            "processed_at",
            "external_reference",
        ]
    )

    EventPublisher.publish(
        EventFactory.withdrawal_completed(
            withdrawal
        )
    )

    return withdrawal
