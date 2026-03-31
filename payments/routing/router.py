from payments.models.gateway import PaymentGateway


class PaymentRouter:

    @staticmethod
    def select_gateway(country_iso=None, gateway_name=None):

        gateway_qs = PaymentGateway.objects.filter(
            is_active=True
        ).order_by("priority")

        if gateway_name:
            gateway_qs = gateway_qs.filter(name=gateway_name)

        if country_iso:
            filtered = gateway_qs.filter(
                countries_allowed__iso_code=country_iso
            )
            if filtered.exists():
                gateway_qs = filtered

        if not gateway_qs.exists():
            raise Exception("No gateway available")

        gateway_config = gateway_qs.first()

        module_path, class_name = gateway_config.gateway_class_path.rsplit(".", 1)

        module = __import__(module_path, fromlist=[class_name])
        gateway_class = getattr(module, class_name)

        # ⭐ فقط instance برگردون
        return gateway_class(config=gateway_config)
