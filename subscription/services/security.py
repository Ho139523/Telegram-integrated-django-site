import hashlib
import hmac
import json
import uuid
from django.conf import settings


class PaymentSecurity:

    @staticmethod
    def sign_payload(payload):

        body_str = json.dumps(
            payload,
            separators=(",", ":"),
            ensure_ascii=False
        )

        body = body_str.encode("utf-8")

        ts = str(int(__import__("time").time()))

        message = f"{ts}.{body_str}".encode()

        signature = hmac.new(
            settings.BOT_SECRET_KEY.encode(),
            message,
            hashlib.sha256
        ).hexdigest()

        return ts, signature, body
