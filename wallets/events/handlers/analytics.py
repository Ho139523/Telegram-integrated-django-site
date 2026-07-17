from wallets.events.handlers.base import BaseEventHandler


class AnalyticsHandler(BaseEventHandler):

    priority = 30

    critical = False

    retryable = True

    name = "Analytics"

    def handle(self, event):

        print(
            f"[ANALYTICS] {event}"
        )
