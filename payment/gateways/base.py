from abc import ABC, abstractmethod


class BaseGateway(ABC):

    @abstractmethod
    def send_request(
        self,
        *,
        amount,
        description,
        email=None,
        mobile=None,
    ):
        """
        ایجاد درخواست پرداخت.
        """
        raise NotImplementedError

    @abstractmethod
    def verify(
        self,
        *,
        authority,
        amount,
    ):
        """
        تأیید پرداخت.
        """
        raise NotImplementedError
