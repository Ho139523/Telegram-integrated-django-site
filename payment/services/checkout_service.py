from django.core.cache import cache
from django.http import JsonResponse, HttpResponse

from payment.models import (
    Transaction,
    Cart,
    CartItem,
)

from accounts.models import ProfileModel

from payment.gateways import ZarinPal


class CheckoutService:

    def __init__(self):

        self.gateway = ZarinPal()

    def create_payment(
        self,
        *,
        payment_id,
    ):

        payment_cache_key = (
            f"payment_{payment_id}"
        )

        payment_data = cache.get(
            payment_cache_key
        )

        if not payment_data:

            return JsonResponse(
                {
                    "error":
                    "لینک پرداخت منقضی شده است"
                },
                status=400
            )

        tel_id = payment_data["tel_id"]

        profile = ProfileModel.objects.get(
            tel_id=tel_id
        )

        cart = Cart.objects.get(
            profile=profile
        )

        cart_items = list(
            CartItem.objects
            .filter(
                cart=cart
            )
            .select_related(
                "product",
                "product__store",
                "product__store__currency",
                "variant",
            )
        )

        if not cart_items:

            return JsonResponse(
                {
                    "error":
                    "سبد خرید خالی است"
                },
                status=400
            )

        currency_ids = {
            item.product.store.currency_id
            for item in cart_items
        }

        if len(currency_ids) != 1:

            return JsonResponse(
                {
                    "error":
                    "تمام کالاهای سبد باید یک ارز داشته باشند."
                },
                status=400
            )

        currency_id = next(
            iter(currency_ids)
        )

        total_amount = sum(
            item.total_price()
            for item in cart_items
        )

        if total_amount <= 0:

            return JsonResponse(
                {
                    "error":
                    "مبلغ پرداخت نامعتبر است"
                },
                status=400
            )

        transaction = Transaction.objects.create(
            profile=profile,
            cart=cart,
            amount=total_amount,
            currency_id=currency_id,
            status="pending",
        )

        response = self.gateway.send_request(
            amount=int(
                total_amount * 10
            ),
            description=(
                f"پرداخت سبد خرید شامل "
                f"{len(cart_items)} کالا"
            ),
            mobile=profile.phone,
        )

        if not response.get("success"):

            transaction.status = "failed"

            transaction.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            return JsonResponse(
                {
                    "error":
                    response.get(
                        "message",
                        "خطا در اتصال به درگاه"
                    )
                },
                status=400
            )

        authority = response.get(
            "authority"
        )

        if not authority:

            transaction.status = "failed"

            transaction.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            return JsonResponse(
                {
                    "error":
                    "Authority دریافت نشد"
                },
                status=400
            )

        transaction.authority = authority

        transaction.save(
            update_fields=[
                "authority",
                "updated_at",
            ]
        )

        cache.delete(
            payment_cache_key
        )

        return self._payment_page(
            response["url"]
        )

    def _payment_page(
        self,
        payment_url
    ):

        html = f"""
        <!DOCTYPE html>

        <html lang="fa">

        <head>

            <meta charset="UTF-8">

            <meta
                name="viewport"
                content="width=device-width,
                initial-scale=1.0"
            >

            <title>
                انتقال به درگاه پرداخت
            </title>

        </head>

        <body>

            <p>
                در حال انتقال به درگاه پرداخت...
            </p>

            <a href="{payment_url}">
                ورود به درگاه پرداخت
            </a>

            <script>

                const paymentUrl =
                    "{payment_url}";

                if (
                    window.Telegram &&
                    Telegram.WebApp &&
                    Telegram.WebApp.openLink
                ) {{

                    Telegram.WebApp.openLink(
                        paymentUrl,
                        {{
                            try_instant_view: false
                        }}
                    );

                    setTimeout(
                        () => {{
                            Telegram.WebApp.close();
                        }},
                        500
                    );

                }} else {{

                    window.location.replace(
                        paymentUrl
                    );

                }}

            </script>

        </body>

        </html>
        """

        return HttpResponse(
            html
        )
