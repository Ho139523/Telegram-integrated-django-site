# wallets/services/summary.py


from decimal import Decimal

from wallets.models import WalletBalance


def wallet_summary(
    *,
    wallet,
    currency,
):

    balance = (
        WalletBalance.objects
        .filter(
            wallet=wallet,
            currency=currency,
        )
        .first()
    )

    if balance is None:

        return {
            "available": Decimal("0"),
            "pending": Decimal("0"),
            "locked": Decimal("0"),
            "total": Decimal("0"),
        }

    return {

        "available": balance.available,

        "pending": balance.pending,

        "locked": balance.locked,

        "total": (
            balance.available
            + balance.pending
            + balance.locked
        ),
    }
