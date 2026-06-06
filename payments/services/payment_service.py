from django.contrib.contenttypes.models import ContentType
from payments.models.intent import PaymentIntent
from payments.routing.router import PaymentRouter
from payments.services.gateway_engine import GatewayExecutionEngine
from payments.services import PaymentIntelligenceBrain
from payments.serializers import PaymentIntentSerializer
from django.utils import timezone
from datetime import timedelta


class PaymentService:

    @staticmethod
    def create_payment(
        profile,
        amount,
        target,
        country_iso,
        ip,
        gateway_name=None,
        metadata=None
    ):
    
        brain_result = PaymentIntelligenceBrain.process_payment_request(
            profile=profile,
            amount=amount,
            target=target,
            requested_country=country_iso,
            ip=ip,
            gateway_name=gateway_name
        )
    
        if brain_result["status"] != "ok":
            return brain_result
    
        if brain_result["status"] != "ok":
            return brain_result
        
        gateway_instance = brain_result.get("gateway_instance")
        if not gateway_instance:
            return {
                "status": "no_gateway",
                "message": "Gateway routing failed"
            }
    
        content_type = ContentType.objects.get_for_model(target)
    
        intent = PaymentIntent.objects.create(
            profile=profile,
            amount=amount,
            currency="IRR",
            status="created",
            gateway=gateway_instance.__class__.__name__,
            content_type=content_type,
            object_id=target.id,
            metadata=metadata or {},
            expires_at=timezone.now() + timedelta(hours=1)
        )
    
        # ⭐ اجرای پرداخت روی gateway
        result = GatewayExecutionEngine.execute(
            intent,
            gateway_instance,
            action="create"
        )
    
        # ⭐ ذخیره URL پرداخت داخل metadata
        payment_url = result.get("payment_url")
    
        if payment_url:
            intent.metadata["payment_url"] = payment_url
            intent.save(update_fields=["metadata"])
    
        return {
            "status": "ok",
            "intent": intent,
            "payment_url": payment_url
        }
