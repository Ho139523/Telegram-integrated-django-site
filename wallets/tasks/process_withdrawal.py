# wallets/tasks/process_withdrawal.py

import asyncio
import logging

from wallets.providers.factory import (
    WithdrawalProviderFactory,
)

from wallets.services.withdrawal_process import (
    start_withdrawal_processing,
)

from wallets.services.withdrawal_complete import (
    complete_withdrawal,
)

from wallets.services.withdrawal_fail import (
    fail_withdrawal,
)


logger = logging.getLogger(__name__)


def process_withdrawal(
    withdrawal_id,
):
    """
    Process one withdrawal through its provider.

    Flow:

        PENDING
            ↓
        PROCESSING
            ↓
        provider.transfer()   [ASYNC boundary]
            ↓
        COMPLETED / FAILED / PROCESSING

    The surrounding Django/database logic remains synchronous.
    Only the external provider call is asynchronous.
    """

    # --------------------------------------------------
    # 1. Atomically claim withdrawal
    # --------------------------------------------------

    withdrawal = (
        start_withdrawal_processing(
            withdrawal_id
        )
    )

    if withdrawal is None:
        return None

    # --------------------------------------------------
    # 2. Resolve provider
    # --------------------------------------------------

    provider = (
        WithdrawalProviderFactory.get(
            withdrawal.provider
        )
    )

    # --------------------------------------------------
    # 3. Call async provider
    # --------------------------------------------------

    try:

        result = asyncio.run(
            provider.transfer(
                amount=withdrawal.amount,
                destination=withdrawal.destination,
                reference=str(withdrawal.pk),
            )
        )

    except Exception:

        logger.exception(
            "Withdrawal provider error. "
            "withdrawal_id=%s",
            withdrawal.pk,
        )

        #
        # IMPORTANT:
        #
        # We do NOT mark the withdrawal as failed.
        #
        # A network error does not prove that the
        # external transfer did not happen.
        #
        return withdrawal

    # --------------------------------------------------
    # 4. Provider confirmed success
    # --------------------------------------------------

    if result.status == "completed":

        return complete_withdrawal(
            withdrawal,
            external_reference=(
                result.external_reference
            ),
        )

    # --------------------------------------------------
    # 5. Provider explicitly rejected the transfer
    # --------------------------------------------------

    if result.status == "failed":

        return fail_withdrawal(
            withdrawal
        )

    # --------------------------------------------------
    # 6. Processing / unknown
    # --------------------------------------------------

    #
    # Keep money locked.
    #

    return withdrawal
