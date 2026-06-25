import json
import requests

from django.conf import settings

class ZarinPal:

    def __init__(self):  

        config = settings.ZARINPAL  

        self.callback_url = config["CALLBACK_URL"]  
        self.sandbox = config["SANDBOX"]  
        self.merchant_id = config["MERCHANT_ID"]  

        gateway = "https://www.zarinpal.com" 

        if self.sandbox:  

            self.request_url = (  
                "https://sandbox.zarinpal.com/pg/v4/payment/request.json"  
            )  

            self.verify_url = (  
                "https://sandbox.zarinpal.com/pg/v4/payment/verify.json"  
            )  

            self.startpay_url = (  
                "https://sandbox.zarinpal.com/pg/StartPay/{authority}"  
            )  

        else:  

            self.request_url = (  
                "https://api.zarinpal.com/pg/v4/payment/request.json"  
            )  

            self.verify_url = (  
                "https://api.zarinpal.com/pg/v4/payment/verify.json"  
            )  

            # استفاده از دامنه اختصاصی  
            self.startpay_url = (  
                f"{gateway}/pg/StartPay/{{authority}}"  
            )  

    def send_split_request(  
        self,  
        amount,  
        description,  
        splits=None,  
        email=None,  
        mobile=None,  
    ):  

        if splits is None:  
            splits = []  

        payload = {  
            "merchant_id": self.merchant_id,  
            "amount": int(amount),  
            "callback_url": self.callback_url,  
            "description": description,  
            "metadata": {  
                "mobile": str(mobile) if mobile else "",  
                "email": email or "",  
            }  
        }  

        # پرداخت چندفروشنده  
        if splits:  
            payload["wages"] = splits  

        headers = {  
            "accept": "application/json",  
            "content-type": "application/json",  
        }  

        try:  

            print("=" * 50)  
            print("ZARINPAL REQUEST")  
            print(json.dumps(payload, indent=2, ensure_ascii=False))  
            print("=" * 50)  

            response = requests.post(  
                self.request_url,  
                json=payload,  
                headers=headers,  
                timeout=30  
            )  

            print("STATUS:", response.status_code)  
            print("BODY:", response.text)  

            data = response.json()  

            if (  
                response.status_code == 200  
                and "data" in data  
                and "authority" in data["data"]  
            ):  

                authority = data["data"]["authority"]  

                payment_url = self.startpay_url.format(  
                    authority=authority  
                )  

                return {  
                    "success": True,  
                    "authority": authority,  
                    "url": payment_url,  
                }  

            errors = data.get("errors", {})  

            return {  
                "success": False,  
                "message": errors.get(  
                    "message",  
                    "Unknown error"  
                ),  
                "error_code": errors.get("code"),  
            }  

        except Exception as e:  

            return {  
                "success": False,  
                "message": str(e),  
            }  

    def send_request(  
        self,  
        amount,  
        description,  
        email=None,  
        mobile=None,  
    ):  

        return self.send_split_request(  
            amount=amount,  
            description=description,  
            splits=[],  
            email=email,  
            mobile=mobile,  
        )  

    def verify(self, authority, amount):  

        payload = {  
            "merchant_id": self.merchant_id,  
            "authority": authority,  
            "amount": int(amount),  
        }  

        try:  

            response = requests.post(  
                self.verify_url,  
                json=payload,  
                timeout=30  
            )  

            data = response.json()  

            print("VERIFY RESPONSE:")  
            print(data)  

            if (  
                response.status_code == 200  
                and data["data"]["code"] == 100  
            ):  

                return {  
                    "success": True,  
                    "ref_id": data["data"]["ref_id"],  
                    "fee": data["data"]["fee"],  
                    "fee_type": data["data"]["fee_type"],  
                }  

            return {  
                "success": False,  
                "message": data.get(  
                    "errors",  
                    {}  
                ).get(  
                    "message",  
                    "Verification failed"  
                )  
            }  

        except Exception as e:  

            return {  
                "success": False,  
                "message": str(e)  
            }
