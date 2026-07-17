from decimal import Decimal
from uuid import uuid4

from django.test import TestCase

from accounts.models import ProfileModel

from wallets.models import Currency

from wallets.services import (
    sale_pending,
    sale_release,
)

from wallets.services.treasury import (
    get_treasury_wallet,
)


class IdempotentSaleReleaseTests(TestCase):

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

    def test_duplicate_sale_release_is_ignored(self):

        sale_pending(
            seller_wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("100"),
        )

        operation_id = uuid4()

        sale_release(
            seller_wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("100"),
            commission=Decimal("5"),
            operation_id=operation_id,
        )

        sale_release(
            seller_wallet=self.wallet,
            currency=self.currency,
            amount=Decimal("100"),
            commission=Decimal("5"),
            operation_id=operation_id,
        )

        seller_balance = self.wallet.balances.get(
            currency=self.currency
        )

        treasury_balance = (
            get_treasury_wallet()
            .balances
            .get(currency=self.currency)
        )

        self.assertEqual(
            seller_balance.available,
            Decimal("95"),
        )

        self.assertEqual(
            treasury_balance.available,
            Decimal("5"),
        )
