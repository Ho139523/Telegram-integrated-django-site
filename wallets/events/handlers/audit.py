from wallets.events.handlers.base import BaseEventHandler


class AuditHandler(BaseEventHandler):

    priority = 20

    critical = False

    retryable = True

    name = "Audit"

    def handle(self, event):

        print(
            f"[AUDIT] {event}"
        )
