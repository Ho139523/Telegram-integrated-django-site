import time
import logging
from payments.models.attempt import PaymentAttempt


logger = logging.getLogger(__name__)


class GatewayExecutionEngine:

    MAX_RETRY = 3
    TIMEOUT = 10

    @staticmethod
    def execute(intent, gateway_instance, action="create"):

        for attempt_number in range(GatewayExecutionEngine.MAX_RETRY):

            try:
                start_time = time.time()

                if action == "create":
                    result = gateway_instance.create_payment(intent)

                elif action == "verify":
                    result = gateway_instance.verify_payment(intent)

                else:
                    raise Exception("Invalid action")

                duration = time.time() - start_time

                logger.info(
                    f"Gateway execution success: {gateway_instance.__class__.__name__}"
                )

                return result

            except Exception as e:

                logger.error(f"Gateway error: {str(e)}")

                if attempt_number == GatewayExecutionEngine.MAX_RETRY - 1:
                    raise

                time.sleep(2 ** attempt_number)  # exponential backoff

