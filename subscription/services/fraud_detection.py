import time
from django.conf import settings


class FraudDetectionService:

    @staticmethod
    def check_payment_fraud(payment, request_ip=None):

        risk_score = 0

        # ⭐ Rule 1 — Too Fast Payment
        if payment.created_at:
            if time.time() - payment.created_at.timestamp() < 10:
                risk_score += 40

        # ⭐ Rule 2 — Multiple Payment Attempts
        if payment.transaction_set.count() > 3:
            risk_score += 30

        # ⭐ Rule 3 — IP based anomaly (optional)
        # if request_ip and request_ip in suspicious_ips:
        #     risk_score += 50

        return risk_score

    @staticmethod
    def is_fraud(payment):

        score = FraudDetectionService.check_payment_fraud(payment)

        return score > 60
