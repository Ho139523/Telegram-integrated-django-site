from django.conf import settings

from payment.gateways import ZarinPal


class CheckoutService:

    def __init__(self):

        self.gateway = ZarinPal()

    def create_payment(self, profile, cart):

        """
        ساخت تراکنش پرداخت
        """

        raise NotImplementedError
