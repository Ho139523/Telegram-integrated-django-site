from abc import ABC, abstractmethod


class BaseGateway(ABC):

    @abstractmethod
    def send_request(self, *args, **kwargs):
        pass

    @abstractmethod
    def verify(self, *args, **kwargs):
        pass
