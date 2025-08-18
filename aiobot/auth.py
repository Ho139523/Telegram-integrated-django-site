# aiobot    /auth.py
import time
import hmac
import hashlib

from django.conf import settings
from rest_framework.permissions import BasePermission
from django_redis import get_redis_connection  # optional, برای nonce

class BotSignaturePermission(BasePermission):
    message = "Invalid bot signature"

    def _check_nonce(self, nonce: str) -> bool:
        if not nonce:
            return True
        try:
            conn = get_redis_connection("default")
            key = f"bot:nonce:{nonce}"
            # اگر قبلا وجود داشته، setnx برمی‌گرداند False -> replay
            created = conn.set(key, 1, ex=settings.BOT_NONCE_EXPIRES, nx=True)
            return bool(created)
        except Exception:
            # اگر redis در دسترس نبود، می‌تونی تصمیم بگیری که رد کنی یا قبول کنی.
            # برای آغاز، بهتره قبول کن ولی در Production بهتره Redis داشته باشی.
            return True

    def has_permission(self, request, view):
        sig = request.headers.get("X-Bot-Signature")
        ts = request.headers.get("X-Bot-Timestamp")
        nonce = request.headers.get("X-Bot-Nonce")

        if not sig or not ts:
            return False

        try:
            ts_int = int(ts)
        except ValueError:
            return False

        # 1) cheap check: timestamp window
        if abs(time.time() - ts_int) > settings.BOT_SIGNATURE_EXPIRES:
            return False

        # 2) optional nonce check (prevent replay)
        if nonce:
            if not self._check_nonce(nonce):
                return False

        # 3) compute HMAC on raw body (request.body)
        try:
            secret = settings.BOT_SECRET_KEY.encode()
            body = request.body or b""
            msg = ts.encode() + b"." + body
            expected = hmac.new(secret, msg, hashlib.sha256).hexdigest()
            # constant-time compare
            return hmac.compare_digest(expected, sig)
        except Exception:
            return False
