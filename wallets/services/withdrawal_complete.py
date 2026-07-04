# wallets/services/withdrawal_complete.py

from django.db import transaction
from django.utils import timezone

from wallets.models import (
    Withdrawal,
    WalletBalance,
)


@transaction.atomic
def complete_withdrawal(
    withdrawal: Withdrawal,
    external_reference: str | None = None,
):

    withdrawal = (
        Withdrawal.objects
        .select_for_update()
        .get(pk=withdrawal.pk)
    )

    if withdrawal.status != Withdrawal.Status.PENDING:
        raise ValueError(
            "Withdrawal is not pending."
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
        update_fields=["locked"]
    )

    withdrawal.status = Withdrawal.Status.COMPLETED
    withdrawal.processed_at = timezone.now()

    if external_reference:
        withdrawal.external_reference = external_reference

    withdrawal.save(
        update_fields=[
            "status",
            "processed_at",
            "external_reference",
        ]
    )

    return withdrawal
