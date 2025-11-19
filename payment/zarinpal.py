import requests
import json
from django.conf import settings

class ZarinPal:
    def __init__(self):
        self.callbackURL = settings.ZARINPAL['CALLBACK_URL']
        self.sandbox = settings.ZARINPAL['SANDBOX']
        self.merchant_id = settings.ZARINPAL['MERCHANT_ID']

        if self.sandbox:
            self.ZP_API_REQUEST = "https://sandbox.zarinpal.com/pg/v4/payment/request.json"
            self.ZP_API_STARTPAY = "https://sandbox.zarinpal.com/pg/StartPay/{authority}"
            self.ZP_API_VERIFY = "https://sandbox.zarinpal.com/pg/v4/payment/verify.json"
        else:
            self.ZP_API_REQUEST = "https://api.zarinpal.com/pg/v4/payment/request.json"
            self.ZP_API_STARTPAY = "https://www.zarinpal.com/pg/StartPay/{authority}"
            self.ZP_API_VERIFY = "https://api.zarinpal.com/pg/v4/payment/verify.json"

    def send_split_request(self, amount, description, splits, email=None, mobile=None):
        """
        ارسال درخواست پرداخت با قابلیت تقسیم
        
        :param splits: لیستی از دیکشنری‌های تقسیم پرداخت
        مثال: [
            {"merchant_id": "merchant1", "amount": 50000},
            {"merchant_id": "merchant2", "amount": 30000}
        ]
        """
        req_data = {
            "merchant_id": self.merchant_id,
            "amount": amount,
            "callback_url": self.callbackURL,
            "description": description,
            "metadata": {
                "mobile": str(mobile) if mobile else "",
                "email": email
            }
        }
        
        # اضافه کردن تقسیم‌های پرداخت اگر وجود داشته باشند
        if splits:
            req_data["wages"] = splits

        req_header = {"accept": "application/json", "content-type": "application/json"}

        try:
            response = requests.post(url=self.ZP_API_REQUEST, data=json.dumps(req_data), headers=req_header)
            res_json = response.json()

            if response.status_code == 200 and "data" in res_json and "authority" in res_json["data"]:
                authority = res_json["data"]["authority"]
                return {
                    "success": True,
                    "authority": authority,
                    "url": self.ZP_API_STARTPAY.format(authority=authority)
                }
            else:
                error_message = res_json.get("errors", {}).get("message", "Unknown error from ZarinPal")
                error_code = res_json.get("errors", {}).get("code", 0)
                return {
                    "success": False,
                    "message": error_message,
                    "error_code": error_code
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection error: {str(e)}"
            }

    def send_request(self, amount, description, email=None, mobile=None):
        """درخواست پرداخت ساده (بدون تقسیم)"""
        return self.send_split_request(amount, description, [], email, mobile)

    def verify(self, authority, amount):
        """تایید پرداخت"""
        req_data = {
            "merchant_id": self.merchant_id,
            "amount": amount,
            "authority": authority
        }
        req_header = {"accept": "application/json", "content-type": "application/json"}

        try:
            response = requests.post(url=self.ZP_API_VERIFY, data=json.dumps(req_data), headers=req_header)
            res_json = response.json()

            if response.status_code == 200 and "data" in res_json:
                data = res_json["data"]
                if data.get("code") == 100:
                    return {
                        "success": True,
                        "transaction": True,
                        "pay": True,
                        "ref_id": data.get("ref_id"),
                        "fee": data.get("fee"),
                        "fee_type": data.get("fee_type")
                    }
                else:
                    return {
                        "success": False,
                        "transaction": False,
                        "status": data.get("code"),
                        "message": data.get("message", "Verification failed")
                    }
            else:
                return {
                    "success": False,
                    "transaction": False,
                    "status": res_json.get("status", "error"),
                    "message": res_json.get("errors", {}).get("message", "Unknown error")
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection error: {str(e)}"
            }