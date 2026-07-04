# wallets/tests/test_sale_refund.py

from decimal import Decimal

from django.test import TestCase

from accounts.models import ProfileModel

from wallets.models import Currency

from wallets.services import (
    sale_pending,
    sale_refund,
)




class SaleRefundTests(TestCase):

    def setUp(self):

        self.currency = Currency.objects.create(
            code="USD",
            name="US Dollar",
            symbol="$",
        )


        self.seller_wallet = ProfileModel.objects.create(
            tel_id="10001",
            fname="Seller",
        ).wallet

        self.buyer_wallet = ProfileModel.objects.create(
            tel_id="10002",
            fname="Buyer",
        ).wallet

    def test_sale_refund(self):

        sale_pending(
            seller_wallet=self.seller_wallet,
            currency=self.currency,
            amount=Decimal("100"),
        )

        sale_refund(
            seller_wallet=self.seller_wallet,
            buyer_wallet=self.buyer_wallet,
            currency=self.currency,
            amount=Decimal("100"),
        )

        seller_balance = self.seller_wallet.balances.get(
            currency=self.currency
        )

        buyer_balance = self.buyer_wallet.balances.get(
            currency=self.currency
        )

        self.assertEqual(
            seller_balance.pending,
            Decimal("0")
        )

        self.assertEqual(
            buyer_balance.available,
            Decimal("100")
        )

    def test_cannot_refund_more_than_pending(self):

        sale_pending(
            seller_wallet=self.seller_wallet,
            currency=self.currency,
            amount=Decimal("50"),
        )

        with self.assertRaises(ValueError):

            sale_refund(
                seller_wallet=self.seller_wallet,
                buyer_wallet=self.buyer_wallet,
                currency=self.currency,
                amount=Decimal("100"),
            )
