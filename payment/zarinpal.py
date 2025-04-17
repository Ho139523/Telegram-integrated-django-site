import requests
import json
from django.conf import settings


class ZarinPal:
    def __init__(self):
        self.MERCHANT = settings.ZARINPAL['MERCHANT_ID']
        self.callbackURL = settings.ZARINPAL['CALLBACK_URL']
        self.sandbox = settings.ZARINPAL['SANDBOX']

        if self.sandbox:
            self.ZP_API_REQUEST = "https://sandbox.zarinpal.com/pg/v4/payment/request.json"
            self.ZP_API_STARTPAY = "https://sandbox.zarinpal.com/pg/StartPay/{authority}"
            self.ZP_API_VERIFY = "https://sandbox.zarinpal.com/pg/v4/payment/verify.json"
        else:
            self.ZP_API_REQUEST = "https://api.zarinpal.com/pg/v4/payment/request.json"
            self.ZP_API_STARTPAY = "https://www.zarinpal.com/pg/StartPay/{authority}"
            self.ZP_API_VERIFY = "https://api.zarinpal.com/pg/v4/payment/verify.json"

    def send_request(self, amount, description, email=None, mobile=None):
        req_data = {
            "merchant_id": self.MERCHANT,
            "amount": amount,
            "callback_url": self.callbackURL,
            "description": description,
            "metadata": {"mobile": str(mobile) if mobile else "", "email": email}
        }

        req_header = {"accept": "application/json", "content-type": "application/json"}

        response = requests.post(url=self.ZP_API_REQUEST, data=json.dumps(req_data), headers=req_header)
        res_json = response.json()

        if "data" in res_json and "authority" in res_json["data"]:
            authority = res_json["data"]["authority"]
            return {
                "authority": authority,
                "url": self.ZP_API_STARTPAY.format(authority=authority)
            }
        else:
            return {"message": res_json.get("errors", {}).get("message", "Unknown error"), "error_code": res_json.get("errors", {}).get("code", 0)}

    def verify(self, authority, amount):
        req_data = {
            "merchant_id": self.MERCHANT,
            "amount": amount,
            "authority": authority
        }
        req_header = {"accept": "application/json", "content-type": "application/json"}

        response = requests.post(url=self.ZP_API_VERIFY, data=json.dumps(req_data), headers=req_header)
        res_json = response.json()

        if "data" in res_json and res_json["data"].get("code") == 100:
            return {"transaction": True, "pay": True, "RefID": res_json["data"]["ref_id"]}
        else:
            return {"transaction": False, "status": res_json.get("status", "error"), "message": res_json.get("errors", {}).get("message", "Unknown error")}
