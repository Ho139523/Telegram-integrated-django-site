# wallets/services/idempotency.py

from django.contrib.contenttypes.models import ContentType

from wallets.models import IdempotencyKey


def get_cached_result(
    *,
    key,
    service,
):

    if key is None:
        return None

    record = (
        IdempotencyKey.objects
        .filter(
            key=key,
            service=service,
        )
        .select_related("content_type")
        .first()
    )

    if record:
        return record.content_object

    return None


def save_result(
    *,
    key,
    service,
    obj,
):

    if key is None:
        return obj

    IdempotencyKey.objects.create(
        key=key,
        service=service,
        content_type=ContentType.objects.get_for_model(obj),
        object_id=obj.pk,
    )

    return obj
