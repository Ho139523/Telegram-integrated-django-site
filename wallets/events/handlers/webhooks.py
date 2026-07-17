from wallets.events.handlers.base import BaseEventHandler


class WebhookHandler(BaseEventHandler):

    priority = 50

    critical = False

    retryable = True

    name = "Webhook"

    def handle(self, event):

        print(
            f"[WEBHOOK] {event}"
        )
