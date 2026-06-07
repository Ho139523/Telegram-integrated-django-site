from payments.gateways.base import BasePaymentGateway
from django.conf import settings
import requests
from payments.models.attempt import PaymentAttempt


class ZarinpalGateway(BasePaymentGateway):

    def create_payment(self, intent):

        url = "https://sandbox.zarinpal.com/pg/v4/payment/request.json"

        payload = {
            "merchant_id": settings.ZARINPAL["MERCHANT_ID"],
            "amount": int(intent.amount),
            "callback_url": settings.ZARINPAL["CALLBACK_URL"],
            "description": f"Payment {intent.intent_id}"
        }

        print(settings.ZARINPAL["CALLBACK_URL"])
        response = requests.post(url, json=payload)
        data = response.json()

        if response.status_code == 200 and "data" in data:

            authority = data["data"]["authority"]

            PaymentAttempt.objects.create(
                intent=intent,
                gateway="zarinpal",
                authority=authority,
                raw_response=data,
                status="created"
            )

            return {
                "payment_url":
                    f"https://sandbox.zarinpal.com/pg/StartPay/{authority}",
                "authority": authority
            }

        raise Exception("Zarinpal create payment failed")

    # ⭐ مهم برای verify callback
    def verify_payment(self, attempt, status=None):

        if status != "OK":
            attempt.status = "failed"
            attempt.save()
            return False

        url = "https://sandbox.zarinpal.com/pg/v4/payment/verify.json"

        payload = {
            "merchant_id": settings.ZARINPAL["MERCHANT_ID"],
            "amount": attempt.intent.amount,
            "authority": attempt.authority
        }

        response = requests.post(url, json=payload)
        data = response.json()

        if response.status_code == 200 and data.get("data", {}).get("code") == 100:

            attempt.status = "verified"
            attempt.raw_verify_response = data
            attempt.save()

            intent = attempt.intent
            intent.status = "succeeded"
            intent.save()

            return True

        attempt.status = "failed"
        attempt.save()

        return False

    def refund(self, attempt):
        raise NotImplementedError

