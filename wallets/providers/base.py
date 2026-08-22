# wallets/providers/base.py

from abc import ABC, abstractmethod
from decimal import Decimal


class WithdrawalResult:

    def __init__(
        self,
        *,
        status: str,
        external_reference: str | None = None,
        message: str | None = None,
    ):
        self.status = status
        self.external_reference = (
            external_reference
        )
        self.message = message


class BaseWithdrawalProvider(ABC):

    @abstractmethod
    async def transfer(
        self,
        *,
        amount: Decimal,
        destination: str,
        reference: str,
    ) -> WithdrawalResult:
        """
        Request an external payout.

        Possible statuses:

            completed
            failed
            processing

        `processing` must also be used when the provider
        result is unknown and the transfer cannot safely
        be considered failed.
        """

        raise NotImplementedError
