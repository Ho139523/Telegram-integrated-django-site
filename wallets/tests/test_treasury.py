# wallets/tests/test_treasury.py

from decimal import Decimal

from django.test import TestCase
from django.conf import settings

from accounts.models import ProfileModel

from wallets.models import Currency

from wallets.services import (
    sale_pending,
    sale_release,
)

from wallets.services.treasury import (
    get_treasury_wallet,
)


class TreasuryTests(TestCase):

    def setUp(self):

        self.currency = Currency.objects.create(
            code="USD",
            name="US Dollar",
            symbol="$",
        )

        self.seller_profile = ProfileModel.objects.create(
            tel_id="10001",
            fname="Seller",
        )

        self.seller_wallet = self.seller_profile.wallet

    def test_commission_goes_to_treasury(self):

        sale_pending(
            seller_wallet=self.seller_wallet,
            currency=self.currency,
            amount=Decimal("100"),
        )

        sale_release(
            seller_wallet=self.seller_wallet,
            currency=self.currency,
            amount=Decimal("100"),
            commission=Decimal("5"),
        )

        treasury_wallet = get_treasury_wallet()

        seller_balance = self.seller_wallet.balances.get(
            currency=self.currency
        )

        treasury_balance = treasury_wallet.balances.get(
            currency=self.currency
        )

        self.assertEqual(
            seller_balance.pending,
            Decimal("0")
        )

        self.assertEqual(
            seller_balance.available,
            Decimal("95")
        )

        self.assertEqual(
            treasury_balance.available,
            Decimal("5")
        )

    def test_treasury_profile_created_with_settings(self):

        treasury_wallet = get_treasury_wallet()

        profile = treasury_wallet.profile

        self.assertEqual(
            profile.tel_id,
            settings.WALLET_SETTINGS["TREASURY_TEL_ID"]
        )

        self.assertEqual(
            profile.fname,
            settings.WALLET_SETTINGS["TREASURY_FIRST_NAME"]
        )

        self.assertEqual(
            profile.lname,
            settings.WALLET_SETTINGS["TREASURY_LAST_NAME"]
        )
