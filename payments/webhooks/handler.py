from payments.models.attempt import PaymentAttempt
from payments.routing.router import PaymentRouter
from payments.services.gateway_engine import GatewayExecutionEngine


class PaymentWebhookHandler:

    @staticmethod
    def handle_callback(request):

        authority = request.GET.get("Authority")
        status = request.GET.get("Status")

        if status != "OK":
            return False

        try:
            attempt = PaymentAttempt.objects.select_related("intent").get(
                authority=authority
            )

            intent = attempt.intent

            # 🔒 idempotency
            if intent.status == "succeeded":
                return True

            gateway = PaymentRouter.select_gateway(
                None,
                attempt.gateway
            )

            result = GatewayExecutionEngine.execute(
                intent,
                gateway,
                action="verify"
            )

            # 🔥 THIS IS THE ONLY SOURCE OF TRUTH
            if not result.get("success"):
                return False

            # ============================
            # 1. Update payment state
            # ============================
            intent.status = "succeeded"
            intent.save(update_fields=["status"])

            # ============================
            # 2. Emit event (NOT direct logic)
            # ============================
            from subscription.events import PaymentSucceededEvent

            PaymentSucceededEvent.emit(intent)

            return True

        except Exception as e:
            print("[WEBHOOK_ERROR]", e)
            return False