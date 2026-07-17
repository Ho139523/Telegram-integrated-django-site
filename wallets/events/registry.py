# wallets/events/registry.py

from __future__ import annotations

from collections import defaultdict

from wallets.events.handlers.base import (
    BaseEventHandler,
)


class EventRegistry:

    def __init__(self):

        self._handlers = defaultdict(list)

    def register(
        self,
        handler: BaseEventHandler,
    ):
        """
        Register one handler for every event
        declared in handler.handles.
        """

        for event_type in handler.handles:

            self._handlers[event_type].append(
                handler
            )

            #
            # Lower priority executes first.
            #
            self._handlers[event_type].sort(
                key=lambda h: h.priority
            )

    def unregister(
        self,
        handler: BaseEventHandler,
    ):

        for event_type in handler.handles:

            if handler in self._handlers[event_type]:

                self._handlers[event_type].remove(
                    handler
                )

    def get_handlers(
        self,
        event_type,
    ):

        return tuple(
            self._handlers.get(
                event_type,
                ()
            )
        )

    def clear(self):

        self._handlers.clear()

    def __contains__(
        self,
        event_type,
    ):

        return event_type in self._handlers

    def __len__(self):

        return sum(
            len(v)
            for v in self._handlers.values()
        )


registry = EventRegistry()
