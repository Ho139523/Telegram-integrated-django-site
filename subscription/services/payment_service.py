from django.utils import timezone
from datetime import timedelta

from payment.zarinpal import ZarinPal
from subscription.models import Subscription, SubscriptionInvoice
from payment.models import Transaction


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

        response = pay.send_request(
            amount=int(invoice.amount * 10),
            description=f"اشتراک {invoice.subscription.plan}",
            mobile=profile.phone,
            email=profile.email
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
