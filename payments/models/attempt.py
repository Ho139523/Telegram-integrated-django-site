import uuid
from django.db import models


class PaymentAttempt(models.Model):

    intent = models.ForeignKey(
        "payments.PaymentIntent",
        on_delete=models.CASCADE,
        related_name="attempts"
    )

    gateway = models.CharField(max_length=50)

    authority = models.CharField(max_length=100, null=True, blank=True)

    ref_id = models.CharField(max_length=100, null=True, blank=True)

    raw_request = models.JSONField(default=dict)
    raw_response = models.JSONField(default=dict)

    status = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)

