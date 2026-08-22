from decimal import Decimal

from wallets.providers.base import (
    BaseWithdrawalProvider,
    WithdrawalResult,
)


class ZarinpalWithdrawalProvider(
    BaseWithdrawalProvider
):

    async def transfer(
        self,
        *,
        amount: Decimal,
        destination: str,
        reference: str,
    ) -> WithdrawalResult:

        raise NotImplementedError(
            "ZarinPal withdrawal API is not configured yet."
        )
