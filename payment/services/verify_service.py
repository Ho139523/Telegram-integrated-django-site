# payment/services/verify_service.py

from payment.gateways import ZarinPal

from payment.services.order_service import (
    OrderService
)


class VerifyService:

    def __init__(self):

        self.gateway = ZarinPal()

        self.order_service = (
            OrderService()
        )

    def process(
        self,
        *,
        transaction,
        status,
    ):

        if transaction.status == "completed":

            return {
                "template":
                "payment/tel_payment_success.html",

                "context": {
                    "message":
                    "این پرداخت قبلاً با موفقیت پردازش شده است."
                }
            }

        if status != "OK":

            transaction.status = "canceled"

            transaction.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            return {
                "template":
                "payment/tel_payment_failed.html",

                "context": {
                    "message":
                    "پرداخت لغو شد."
                }
            }

        response = self.gateway.verify(
            authority=transaction.authority,
            amount=transaction.amount * 10,
        )

        if not response.get("success"):

            transaction.status = "failed"

            transaction.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            return {
                "template":
                "payment/tel_payment_failed.html",

                "context": {
                    "message":
                    response.get(
                        "message",
                        "خطا در تأیید پرداخت"
                    )
                }
            }

        transaction.status = "paid"

        transaction.zarinpal_ref_id = (
            response.get("ref_id")
        )

        transaction.save(
            update_fields=[
                "status",
                "zarinpal_ref_id",
                "updated_at",
            ]
        )

        self.order_service.finalize(
            transaction
        )

        transaction.status = "completed"

        transaction.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return {
            "template":
            "payment/tel_payment_success.html",

            "context": {
                "ref_id":
                response.get("ref_id"),

                "message":
                "پرداخت با موفقیت انجام شد."
            }
        }
