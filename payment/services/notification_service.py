# payment/services/notification_service.py

class PaymentNotificationService:

    def notify(
        self,
        *,
        transaction,
        sales,
    ):

        self.notify_buyer(
            transaction,
            sales
        )

        self.notify_sellers(
            transaction,
            sales
        )

    def notify_buyer(
        self,
        transaction,
        sales,
    ):

        pass

    def notify_sellers(
        self,
        transaction,
        sales,
    ):

        pass
