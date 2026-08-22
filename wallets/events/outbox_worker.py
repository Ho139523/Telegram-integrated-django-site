# wallets/events/outbox_worker.py

from django.db import transaction
from django.utils import timezone

from wallets.models import OutboxEvent

from wallets.events.bus import event_bus
from wallets.events.deserializer import deserialize


class OutboxWorker:

    DEFAULT_BATCH_SIZE = 100

    @classmethod
    def process(cls, batch_size=None):

        batch_size = (
            batch_size
            or cls.DEFAULT_BATCH_SIZE
        )

        processed = 0

        while processed < batch_size:

            result = cls._process_next_event()

            if not result:
                break

            processed += 1

    @classmethod
    def _process_next_event(cls):

        with transaction.atomic():

            record = (
                OutboxEvent.objects
                .select_for_update(
                    skip_locked=True
                )
                .filter(
                    published=False,
                )
                .order_by("id")
                .first()
            )

            if record is None:
                return False

            try:

                event = deserialize(
                    record.event_type,
                    record.payload,
                )

                event_bus.publish(event)

            except Exception as exc:

                #
                # We are still holding the row lock.
                #
                # Persist the failure while the lock is held.
                #

                record.retries += 1
                record.error = str(exc)

                record.save(
                    update_fields=[
                        "retries",
                        "error",
                    ]
                )

                #
                # Do NOT raise.
                #
                # We want this transaction to commit the
                # retry information.
                #

                return True

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

            return True
