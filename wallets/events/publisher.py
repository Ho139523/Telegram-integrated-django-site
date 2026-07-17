# wallets/events/publisher.py

from wallets.models import OutboxEvent

from wallets.events.serializer import serialize


class EventPublisher:

    @staticmethod
    def publish(event):

        data = serialize(event)

        OutboxEvent.objects.create(
            event_type=data["event_type"],
            payload=data["payload"],
        )
