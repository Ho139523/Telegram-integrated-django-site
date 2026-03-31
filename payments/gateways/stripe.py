from payments.gateways.base import BasePaymentGateway


class StripeGateway(BasePaymentGateway):

    def create_payment(self, intent):
        return {
            "payment_url": "https://stripe.com/pay/" + str(intent.intent_id)
        }

    def verify_payment(self, data):
        pass

    def refund(self, attempt):
        pass

