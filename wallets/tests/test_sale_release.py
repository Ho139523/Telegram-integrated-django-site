# wallets/tests/test_sale_release.py

from decimal import Decimal

from django.test import TestCase

from accounts.models import ProfileModel

from wallets.models import Currency

from wallets.services import (
    sale_pending,
    sale_release,
)




class SaleReleaseTests(TestCase):

    def setUp(self):

        self.currency = Currency.objects.create(
            code="USD",
            name="US Dollar",
            symbol="$",
        )

        self.wallet = ProfileModel.objects.create(
            tel_id="10001",
            fname="Seller",
        ).wallet

    def test_release_sale_funds(self):

        sale_pending(
            seller_wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("100"),
        )

        sale_release(
            seller_wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("100"),
            commission=Decimal("5"),
        )

        balance = self.wallet.balances.get(
            currency=self.currency
        )

        self.assertEqual(
            balance.pending,
            Decimal("0")
        )

        self.assertEqual(
            balance.available,
            Decimal("95")
        )

    def test_commission_cannot_exceed_amount(self):

        sale_pending(
            seller_wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("100"),
        )

        with self.assertRaises(ValueError):

            sale_release(
                seller_wallet=self.wallet,
                currency=self.currency,
                amount=Decimal("100"),
                commission=Decimal("150"),
            )
