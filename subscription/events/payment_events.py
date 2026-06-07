from subscription.tasks import handle_payment_paid_event


class PaymentSucceededEvent:

    @staticmethod
    def emit(intent):
        """
        Dispatch event to business layer
        """

        handle_payment_paid_event.delay({
            "intent_id": str(intent.id),
            "subscription_id": intent.target.subscription.id,
            "amount": intent.amount,
        })