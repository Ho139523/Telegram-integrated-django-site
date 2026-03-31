from abc import ABC, abstractmethod


class BasePaymentGateway(ABC):

    def __init__(self, config=None):
        self.config = config

    @abstractmethod
    def create_payment(self, intent):
        """
        Should return:
        {
            "payment_url": str,
            "authority": str
        }
        """
        pass

    @abstractmethod
    def verify_payment(self, attempt, **kwargs):
        """
        Should return True or False
        """
        pass

    @abstractmethod
    def refund(self, attempt):
        """
        Should process refund and return result
        """
        pass
