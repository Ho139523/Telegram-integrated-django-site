# payment/services/sale_service.py

from decimal import Decimal

from wallets.services.sale_credit import (
    sale_credit,
)


class SaleService:

    @staticmethod
    def create_pending_sale_from_payment(
        *,
        sale,
    ):

        return sale_credit(
            seller_wallet=sale.seller.owner.wallet,
            currency=sale.currency,
            amount=Decimal(
                sale.total_price
            ),
            reference_id=sale.id,
            operation_id=sale.operation_id,
        )
