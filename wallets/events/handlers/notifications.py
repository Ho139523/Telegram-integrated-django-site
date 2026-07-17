from wallets.events.handlers.base import BaseEventHandler


class NotificationHandler(BaseEventHandler):

    priority = 40

    critical = False

    retryable = True

    name = "Notification"

    def handle(self, event):

        print(
            f"[NOTIFICATION] {event}"
        )
