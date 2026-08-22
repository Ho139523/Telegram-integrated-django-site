import requests

from django.conf import settings

from .base import BaseGateway

class ZarinPal(BaseGateway):

def __init__(self):

    config = settings.ZARINPAL

    self.callback_url = config["CALLBACK_URL"]
    self.sandbox = config["SANDBOX"]
    self.merchant_id = config["MERCHANT_ID"]

    if self.sandbox:

        self.request_url = (
            "https://sandbox.zarinpal.com/"
            "pg/v4/payment/request.json"
        )

        self.verify_url = (
            "https://sandbox.zarinpal.com/"
            "pg/v4/payment/verify.json"
        )

        self.startpay_url = (
            "https://sandbox.zarinpal.com/"
            "pg/StartPay/{authority}"
        )

    else:

        self.request_url = (
            "https://api.zarinpal.com/"
            "pg/v4/payment/request.json"
        )

        self.verify_url = (
            "https://api.zarinpal.com/"
            "pg/v4/payment/verify.json"
        )

        self.startpay_url = (
            "https://www.zarinpal.com/"
            "pg/StartPay/{authority}"
        )

# ==========================================================
# PAYMENT REQUEST
# ==========================================================

def send_request(
    self,
    *,
    amount,
    description,
    email=None,
    mobile=None,
):

    payload = {
        "merchant_id": self.merchant_id,
        "amount": int(amount),
        "callback_url": self.callback_url,
        "description": description,
        "metadata": {
            "mobile": (
                str(mobile)
                if mobile
                else ""
            ),
            "email": (
                email
                if email
                else ""
            ),
        },
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
    }

    try:

        print("=" * 50)
        print("ZARINPAL REQUEST")
        print(payload)
        print("=" * 50)

        response = requests.post(
            self.request_url,
            json=payload,
            headers=headers,
            timeout=30,
        )

        print(
            "STATUS:",
            response.status_code,
        )

        print(
            "BODY:",
            response.text,
        )

        try:

            data = response.json()

        except ValueError:

            return {
                "success": False,
                "message": (
                    "پاسخ نامعتبر از درگاه "
                    "پرداخت دریافت شد."
                ),
            }

        response_data = data.get(
            "data",
            {}
        )

        authority = response_data.get(
            "authority"
        )

        if (

            response.status_code == 200
            and authority

        ):

            return {
                "success": True,
                "authority": authority,
                "url": (
                    self.startpay_url
                    .format(
                        authority=authority
                    )
                ),
            }

        errors = data.get(
            "errors",
            {}
        )

        return {
            "success": False,
            "message": (
                errors.get(
                    "message"
                )
                or response_data.get(
                    "message"
                )
                or "خطا در ایجاد درخواست پرداخت."
            ),
            "error_code": (
                errors.get(
                    "code"
                )
                or response_data.get(
                    "code"
                )
            ),
        }

    except requests.RequestException as exc:

        return {
            "success": False,
            "message": (
                "خطا در ارتباط با درگاه "
                "پرداخت."
            ),
            "error": str(exc),
        }

    except Exception as exc:

        return {
            "success": False,
            "message": str(exc),
        }

# ==========================================================
# PAYMENT VERIFICATION
# ==========================================================

def verify(
    self,
    *,
    authority,
    amount,
):

    payload = {
        "merchant_id": self.merchant_id,
        "authority": authority,
        "amount": int(amount),
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
    }

    try:

        response = requests.post(
            self.verify_url,
            json=payload,
            headers=headers,
            timeout=30,
        )

        try:

            data = response.json()

        except ValueError:

            return {
                "success": False,
                "message": (
                    "پاسخ نامعتبر از درگاه "
                    "پرداخت دریافت شد."
                ),
            }

        print("=" * 50)
        print("ZARINPAL VERIFY")
        print(data)
        print("=" * 50)

        response_data = data.get(
            "data",
            {}
        )

        code = response_data.get(
            "code"
        )

        if (

            response.status_code == 200
            and code == 100

        ):

            return {
                "success": True,
                "ref_id": response_data.get(
                    "ref_id"
                ),
                "fee": response_data.get(
                    "fee"
                ),
                "fee_type": response_data.get(
                    "fee_type"
                ),
            }

        errors = data.get(
            "errors",
            {}
        )

        return {
            "success": False,
            "message": (
                errors.get(
                    "message"
                )
                or response_data.get(
                    "message"
                )
                or "تأیید پرداخت ناموفق بود."
            ),
            "error_code": (
                errors.get(
                    "code"
                )
                or code
            ),
        }

    except requests.RequestException as exc:

        return {
            "success": False,
            "message": (
                "خطا در ارتباط با درگاه "
                "پرداخت هنگام تأیید."
            ),
            "error": str(exc),
        }

    except Exception as exc:

        return {
            "success": False,
            "message": str(exc),
        }
