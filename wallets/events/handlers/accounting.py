from wallets.events.handlers.base import BaseEventHandler


class AccountingHandler(BaseEventHandler):

    priority = 10

    critical = True

    retryable = True

    name = "Accounting"

    def handle(self, event):

        print(
            f"[ACCOUNTING] {event}"
        )
