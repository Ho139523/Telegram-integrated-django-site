import uuid
from django.db import models


class PaymentGateway(models.Model):

    name = models.CharField(max_length=100)

    gateway_class_path = models.CharField(max_length=255)

    priority = models.IntegerField(default=1)

    is_active = models.BooleanField(default=True)

    countries_allowed = models.ManyToManyField(
        "payments.Country",
        related_name="gateways"
    )

    def __str__(self):
        return self.name

