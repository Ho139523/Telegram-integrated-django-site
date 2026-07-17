# wallets/events/bus.py

from __future__ import annotations

import logging
import time

from wallets.events.registry import registry


logger = logging.getLogger(__name__)


class EventBus:

    """
    Enterprise synchronous Event Bus.
    """

    def publish(self, event):

        handlers = registry.get_handlers(
            type(event)
        )

        if not handlers:

            logger.debug(
                "No handlers for %s",
                type(event).__name__,
            )

            return

        logger.debug(
            "%s -> %d handler(s)",
            type(event).__name__,
            len(handlers),
        )

        for handler in handlers:

            started = time.perf_counter()

            try:

                logger.debug(
                    "Running %s",
                    handler.name
                    or handler.__class__.__name__,
                )

                handler(event)

            except Exception:

                logger.exception(
                    "Handler %s failed for %s",
                    handler.name
                    or handler.__class__.__name__,
                    type(event).__name__,
                )

                #
                # Critical handler?
                #

                if handler.critical:

                    raise

            finally:

                elapsed = (
                    time.perf_counter()
                    - started
                ) * 1000

                logger.debug(
                    "%s finished in %.2f ms",
                    handler.name
                    or handler.__class__.__name__,
                    elapsed,
                )


event_bus = EventBus()
