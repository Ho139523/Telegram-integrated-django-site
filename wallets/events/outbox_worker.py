from django.db import transaction
from django.utils import timezone

from wallets.models import OutboxEvent

from wallets.events.bus import event_bus
from wallets.events.deserializer import deserialize


class OutboxWorker:
    """
    Reads unpublished events from the Outbox table
    and dispatches them safely.

    Every event is processed in its own transaction.
    """

    DEFAULT_BATCH_SIZE = 100

    @classmethod
    def process(cls, batch_size=None):

        batch_size = batch_size or cls.DEFAULT_BATCH_SIZE

        while True:

            processed = cls._process_batch(batch_size)

            if processed == 0:
                break

    @classmethod
    def _process_batch(cls, batch_size):

        processed = 0

        while processed < batch_size:

            event = cls._lock_next_event()

            if event is None:
                break

            cls._process_event(event)

            processed += 1

        return processed

    @staticmethod
    def _lock_next_event():

        with transaction.atomic():

            return (
                OutboxEvent.objects
                .select_for_update(skip_locked=True)
                .filter(
                    published=False,
                )
                .order_by("id")
                .first()
            )

    @classmethod
    def _process_event(cls, record):

        try:

            event = deserialize(
                record.event_type,
                record.payload,
            )

            event_bus.publish(event)

        except Exception as exc:

            cls._mark_failed(
                record,
                exc,
            )

            return

        cls._mark_published(record)

    @staticmethod
    def _mark_published(record):

        record.published = True
        record.published_at = timezone.now()
        record.error = ""

        record.save(
            update_fields=[
                "published",
                "published_at",
                "error",
            ]
        )

    @staticmethod
    def _mark_failed(record, exc):

        record.retries += 1
        record.error = str(exc)

        record.save(
            update_fields=[
                "retries",
                "error",
            ]
        )
