import redis
import json

redis_client = redis.Redis()

class EventBus:

    @staticmethod
    def publish(event_name, payload):

        redis_client.publish(
            f"events:{event_name}",
            json.dumps(payload)
        )
