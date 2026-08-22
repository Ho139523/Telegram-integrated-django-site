# wallets/tasks/release_sales.py

from celery import shared_task

from django.db import transaction
from django.utils import timezone

from payment.models import Sale

from wallets.services.sale_release import sale_release


@shared_task(
    name="wallets.release_sales"
)
def release_sales():

    now = timezone.now()

    released_count = 0
    failed_count = 0

    failed_ids = set()


    while True:

        with transaction.atomic():

            sale = (
                Sale.objects
                .select_for_update(
                    skip_locked=True
                )
                .filter(
                    release_at__lte=now,
                    released_at__isnull=True,
                )
                .exclude(
                    id__in=failed_ids
                )
                .select_related(
                    "seller",
                    "seller__owner",
                    "seller__owner__wallet",
                    "currency",
                )
                .first()
            )


            if not sale:
                break


            try:

                seller_wallet = (
                    sale.seller.owner.wallet
                )


                if not seller_wallet:
                    raise ValueError(
                        "Seller wallet missing"
                    )


                sale_release(
                    seller_wallet=seller_wallet,
                    currency=sale.currency,
                    amount=sale.total_price,
                    commission=0,
                    reference_id=sale.id,
                    operation_id=sale.release_operation_id,
                )


                sale.released_at = now

                sale.save(
                    update_fields=[
                        "released_at"
                    ]
                )


                released_count += 1


            except Exception as exc:

                failed_count += 1

                failed_ids.add(
                    sale.id
                )


                print(
                    f"Release failed Sale {sale.id}: {exc}"
                )


                continue


    return {
        "released_sales": released_count,
        "failed_sales": failed_count,
    }
