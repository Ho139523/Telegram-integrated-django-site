from payments.routing.geo import GeoIPService
from payments.routing.router import PaymentRouter
from payments.security.fraud import FraudDetector
from payments.security.signature import SignatureValidator
from payments.security.circuit_breaker import CircuitBreaker


class PaymentIntelligenceBrain:

    circuit_breaker = CircuitBreaker()

    @staticmethod
    def process_payment_request(
            profile,
            amount,
            target,
            requested_country,
            ip,
            payload_signature=None,
            gateway_name=None,
            payload=None):

        # ------------------------------------------------
        # Circuit Breaker
        # ------------------------------------------------
        if not PaymentIntelligenceBrain.circuit_breaker.allow_request():
            return {
                "status": "service_unavailable",
                "message": "Payment service temporarily unavailable"
            }

        # ------------------------------------------------
        # Geo Detection
        # ------------------------------------------------
        real_country = GeoIPService.detect_country(ip)

        if real_country and real_country != requested_country:
            risk_score += 20

            return {
                "status": "vpn_warning",
                "real_country": real_country,
                "message": "VPN detected. Please disable VPN."
            }


        # ------------------------------------------------
        # Fraud Detection
        # ------------------------------------------------
        risk_score = FraudDetector.calculate_risk_score(profile, amount)

        if risk_score > 70:
            return {
                "status": "fraud_warning",
                "risk_score": risk_score
            }

        # ------------------------------------------------
        # Signature Validation (خیلی مهم برای Security 🔥)
        # ------------------------------------------------
        if payload_signature and payload:
            if not SignatureValidator.verify(
                payload,
                payload_signature,
                secret="YOUR_SECRET_KEY"
            ):
                return {
                    "status": "invalid_signature"
                }

        # ------------------------------------------------
        # Gateway Routing
        # ------------------------------------------------
        try:
            router_result = PaymentRouter.select_gateway(
                requested_country,
                gateway_name
            )

        except Exception as e:
            PaymentIntelligenceBrain.circuit_breaker.record_failure()

            return {
                "status": "no_gateway",
                "message": str(e)
            }

        return {
            "status": "ok",
            "gateway_instance": router_result,
            "country": requested_country,
            "risk_score": risk_score
        }
