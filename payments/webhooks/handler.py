from payments.models.attempt import PaymentAttempt
from payments.routing.router import PaymentRouter
from payments.services.gateway_engine import GatewayExecutionEngine


class PaymentWebhookHandler:

    @staticmethod
    def handle_callback(request):

        authority = request.GET.get("Authority")
        status = request.GET.get("Status")

        try:
            attempt = PaymentAttempt.objects.get(
                authority=authority
            )

            intent = attempt.intent

            gateway = PaymentRouter.select_gateway(
                None,
                attempt.gateway
            )

            result = GatewayExecutionEngine.execute(
                intent,
                gateway,
                action="verify"
            )

            if result.get("success"):

                intent.status = "succeeded"
                intent.save()

                # ⭐ اینجا مهم است
                PaymentWebhookHandler._post_payment_actions(intent)

                return True

        except Exception as e:
            print(e)

        return False


    # ⭐ این تابع را اینجا می‌گذاریم
    @staticmethod
    def _post_payment_actions(intent):

        target = intent.target

        # اگر target یک مدل business logic داشت
        if hasattr(target, "finalize"):
            target.finalize()

