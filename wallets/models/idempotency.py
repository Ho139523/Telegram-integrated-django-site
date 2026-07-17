from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class IdempotencyKey(models.Model):

    key = models.UUIDField(
        unique=True,
        db_index=True,
    )

    service = models.CharField(
        max_length=64,
        db_index=True,
    )

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
    )

    object_id = models.PositiveBigIntegerField()

    content_object = GenericForeignKey(
        "content_type",
        "object_id",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:

        indexes = [
            models.Index(
                fields=[
                    "service",
                    "key",
                ]
            ),
        ]
