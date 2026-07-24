# payment/services/order_service.py

from decimal import Decimal

from django.db import transaction as db_transaction
from django.db import models

from payment.models import Sale

from products.models import (
    Product,
    ProductVariant,
)

from wallets.models.balance import (
    WalletBalance
)

from payment.services.sale_service import (
    SaleService
)


class OrderService:

    @db_transaction.atomic
    def finalize(
        self,
        transaction,
    ):

        if transaction.status != "paid":

            raise ValueError(
                "Transaction is not paid."
            )

        cart_items = list(
            transaction.cart.items
            .select_related(
                "product",
                "variant",
                "product__store",
                "product__store__owner",
            )
        )

        sales = []

        for cart_item in cart_items:

            product = cart_item.product

            quantity = cart_item.quantity

            variant = cart_item.variant

            # ==========================================
            # 1. مبلغ معتبر است؟
            # ==========================================

            total_price = Decimal(
                cart_item.total_price()
            )

            if total_price <= 0:

                raise ValueError(
                    f"مبلغ محصول "
                    f"{product.name} معتبر نیست."
                )

            # ==========================================
            # 2. بررسی موجودی
            # ==========================================

            has_variants = (
                ProductVariant.objects
                .filter(
                    product=product
                )
                .exists()
            )

            if has_variants:

                if variant:

                    variant = (
                        ProductVariant.objects
                        .select_for_update()
                        .get(
                            pk=variant.pk
                        )
                    )

                else:

                    variant = (
                        ProductVariant.objects
                        .select_for_update()
                        .filter(
                            product=product,
                            stock__gte=quantity,
                        )
                        .first()
                    )

                    if not variant:

                        raise ValueError(
                            f"موجودی محصول "
                            f"{product.name} "
                            f"کافی نیست."
                        )

                    cart_item.variant = variant

                    cart_item.save(
                        update_fields=[
                            "variant"
                        ]
                    )

                if variant.stock < quantity:

                    raise ValueError(
                        f"موجودی واریانت "
                        f"{variant} کافی نیست."
                    )

            else:

                product = (
                    Product.objects
                    .select_for_update()
                    .get(
                        pk=product.pk
                    )
                )

                if product.stock < quantity:

                    raise ValueError(
                        f"موجودی محصول "
                        f"{product.name} کافی نیست."
                    )

            # ==========================================
            # 3. Wallet فروشنده
            # ==========================================

            seller = product.store

            seller_wallet = (
                seller.owner.wallet
            )

            if not seller_wallet:

                raise ValueError(
                    f"فروشنده "
                    f"{seller.owner} "
                    f"Wallet ندارد."
                )

            # ==========================================
            # 4. WalletBalance
            # ==========================================

            balance, created = (
                WalletBalance.objects
                .get_or_create(
                    wallet=seller_wallet,
                    currency=transaction.currency,
                    defaults={
                        "available": 0,
                        "pending": 0,
                    },
                )
            )

            # ==========================================
            # 5. کاهش موجودی
            # ==========================================

            if has_variants:

                variant.stock -= quantity

                variant.save(
                    update_fields=[
                        "stock"
                    ]
                )

                product.refresh_from_db(
                    fields=[
                        "stock"
                    ]
                )

                product.save(
                    system_update=True
                )

            else:

                product.stock -= quantity

                product.save(
                    system_update=True
                )

            # ==========================================
            # 6. ایجاد Sale
            # ==========================================

            sale = Sale.create_from_store(
                transaction=transaction,
                product=product,
                seller=seller,
                quantity=quantity,
                unit_price=int(
                    total_price / quantity
                ),
                total_price=int(
                    total_price
                ),
                variant=variant,
            )

            # ==========================================
            # 7. انتقال به Pending
            # ==========================================

            SaleService.create_pending_sale_from_payment(
                sale=sale
            )

            sales.append(
                sale
            )

        # ==========================================
        # پاک کردن Cart
        # ==========================================

        transaction.cart.items.all().delete()

        return sales
