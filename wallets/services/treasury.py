# wallets/services/treasury.py

from decimal import Decimal

from django.conf import settings
from django.db import transaction

from accounts.models import ProfileModel

from wallets.models import (
    WalletBalance,
    WalletEntry,
)


def get_treasury_wallet():

    config = settings.WALLET_SETTINGS

    profile, _ = ProfileModel.objects.get_or_create(
        tel_id=config["TREASURY_TEL_ID"],
        defaults={
            "fname": config["TREASURY_FIRST_NAME"],
            "lname": config["TREASURY_LAST_NAME"],
            "seller_mode": False,
        }
    )

    return profile.wallet


@transaction.atomic
def credit_commission(
    *,
    currency,
    amount: Decimal,
    reference_id=None,
):

    if amount <= 0:
        raise ValueError(
            "Commission amount must be positive."
        )

    wallet = get_treasury_wallet()

    balance, _ = (
        WalletBalance.objects
        .select_for_update()
        .get_or_create(
            wallet=wallet,
            currency=currency,
        )
    )

    balance.available += amount

    balance.save(
        update_fields=["available"]
    )

    WalletEntry.objects.create(
        wallet=wallet,
        currency=currency,
        amount=amount,
        type=WalletEntry.Type.COMMISSION,
        reference_id=reference_id,
        description="Platform commission received",
    )


def get_treasury_balance(currency):

    wallet = get_treasury_wallet()

    balance, _ = WalletBalance.objects.get_or_create(
        wallet=wallet,
        currency=currency,
    )

    return balance


def get_total_revenue(currency):

    return get_treasury_balance(
        currency
    ).available
