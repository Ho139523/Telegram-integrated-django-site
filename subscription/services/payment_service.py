from django.utils import timezone
from datetime import timedelta

from payment.zarinpal import ZarinPal
from subscription.models import Subscription, SubscriptionInvoice
from payment.models import Transaction

from subscription.services.security import PaymentSecurity
import uuid
from django.db import transaction
from django_redis import get_redis_connection



pay = ZarinPal()


class SubscriptionPaymentService:

    @staticmethod
    def create_invoice(subscription, plan_price, coupon=None):

        amount = plan_price.price

        if coupon and coupon.is_valid():
            if coupon.discount_type == "percent":
                amount -= amount * coupon.value / 100
            else:
                amount -= coupon.value

        invoice = SubscriptionInvoice.objects.create(
            subscription=subscription,
            plan_price=plan_price,
            amount=amount,
            coupon=coupon
        )

        return invoice


    @staticmethod
    def send_payment_request(invoice, profile):

        payload = {
            "invoice_id": invoice.id,
            "amount": float(invoice.amount),
            "user_id": profile.id,
            "idempotency_key": str(uuid.uuid4())
        }

        ts, sig, body = PaymentSecurity.sign_payload(payload)

        headers = {
            "X-Signature": sig,
            "X-Timestamp": ts,
            "Content-Type": "application/json"
        }

        response = pay.send_request(
            amount=int(invoice.amount * 10),
            description=f"اشتراک {invoice.subscription.plan}",
            mobile=profile.phone,
            email=profile.email,
            headers=headers
        )

        if not response["success"]:
            raise Exception("Payment request failed")

        authority = response["authority"]

        txn = Transaction.objects.create(
            profile=profile,
            amount=invoice.amount,
            authority=authority,
            status="pending"
        )

        return response["url"], txn



class InvoiceService:

    @staticmethod
    def change_status(invoice, status):

        valid_transitions = {
            "created": ["pending", "expired"],
            "pending": ["paid", "failed", "expired"],
            "paid": ["completed"],
        }

        if status not in valid_transitions.get(invoice.status, []):
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Invalid state transition")

        invoice.status = status
        invoice.save(update_fields=["status"])


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from subscription.services.event_bus import EventBus
from subscription.services.fraud_detection import FraudDetectionService


class PaymentWebhookView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        # ⭐ Gateway Webhook Data
        authority = request.data.get("Authority")
        status = request.data.get("Status")

        if status != "OK":
            return Response({"status": "failed"}, status=400)

        # ⭐ Payment Lookup
        payment = Payment.objects.select_related(
            "invoice",
            "invoice__subscription",
            "invoice__plan_price"
        ).filter(authority=authority).first()

        if not payment:
            return Response({"error": "payment not found"}, status=404)

        lock_key = f"payment:{authority}"

        # ⭐ Distributed Lock
        with payment_lock(settings.REDIS_CLIENT, lock_key):

            # ⭐ Idempotency Protection
            if payment.status == PaymentState.PAID:
                return Response({"status": "already processed"})

            invoice = payment.invoice
            subscription = invoice.subscription

            # ⭐ Fraud Detection Layer
            if FraudDetectionService.is_fraud(payment):
                payment.status = PaymentState.FAILED
                payment.save(update_fields=["status"])

                return Response(
                    {"error": "fraud detected"},
                    status=403
                )

            # ⭐ Verify Payment Gateway (Optional but recommended)
            # verify_res = pay.verify_payment(authority)
            # if not verify_res["success"]:
            #     return Response({"error": "payment verification failed"}, status=400)

            # ⭐ Business Logic Transaction Safety
            with transaction.atomic():

                InvoiceService.change_status(invoice, "paid")

                # ⭐ Smart Subscription Extend Logic
                base_date = max(
                    subscription.end_date,
                    timezone.now()
                )

                subscription.end_date = base_date + timedelta(
                    days=30 * invoice.plan_price.months
                )

                subscription.status = SubscriptionState.ACTIVE
                subscription.save(update_fields=[
                    "status",
                    "end_date"
                ])

                payment.status = PaymentState.PAID
                payment.save(update_fields=["status"])

                # ⭐ Event Driven Architecture
                transaction.on_commit(lambda: EventBus.publish(
                    "payment_paid",
                    {
                        "subscription_id": subscription.id,
                        "invoice_id": invoice.id
                    }
                ))

                transaction.on_commit(lambda: EventBus.publish(
                    "subscription_activated",
                    {
                        "subscription_id": subscription.id
                    }
                ))

        return Response({"status": "ok"})


from contextlib import contextmanager

@contextmanager
def payment_lock(redis_client, key):

    acquired = redis_client.set(
        key,
        "1",
        nx=True,
        ex=15
    )

    if not acquired:
        raise Exception("Duplicate payment request")

    try:
        yield
    finally:
        redis_client.delete(key)

