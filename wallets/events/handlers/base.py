# wallets/events/handlers/base.py

from __future__ import annotations

from abc import ABC
from abc import abstractmethod


class BaseEventHandler(ABC):
    """
    Base class for all domain event handlers.

    Every handler must inherit from this class.
    """

    #
    # Events handled by this handler.
    # Filled automatically by @handles(...)
    #
    handles = ()

    #
    # Lower number executes first.
    #
    priority: int = 100

    #
    # If True, EventBus stops when this handler fails.
    #
    critical: bool = False

    #
    # Future retry support.
    #
    retryable: bool = True

    #
    # Optional readable name.
    #
    name: str | None = None

    @abstractmethod
    def handle(self, event):
        """
        Process one domain event.
        """
        raise NotImplementedError

    def __call__(self, event):
        """
        Allow handler(event) syntax.
        """
        return self.handle(event)

    def __repr__(self):

        return (
            f"<{self.__class__.__name__}"
            f" priority={self.priority}"
            f" critical={self.critical}>"
        )
