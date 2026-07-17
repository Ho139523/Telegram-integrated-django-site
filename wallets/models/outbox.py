from django.db import models


class OutboxEvent(models.Model):

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    event_type = models.CharField(
        max_length=100,
    )

    payload = models.JSONField()

    published = models.BooleanField(
        default=False,
    )

    published_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    retries = models.PositiveIntegerField(
        default=0,
    )

    error = models.TextField(
        blank=True,
    )

    class Meta:

        ordering = [
            "id",
        ]
