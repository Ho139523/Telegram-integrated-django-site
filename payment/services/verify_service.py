from payment.gateways import ZarinPal


class VerifyService:

    def __init__(self):

        self.gateway = ZarinPal()

    def verify(self, transaction):

        raise NotImplementedError
