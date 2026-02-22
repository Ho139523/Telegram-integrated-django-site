from celery import shared_task
from django.db import transaction

@shared_task
def expire_subscriptions():
    from django.utils import timezone
    from .models import Subscription

    now = timezone.now()

    with transaction.atomic():
        expired = Subscription.objects.select_for_update().filter(
            end_date__lte=now,
            status='active'
        )

        count = expired.count()

        for sub in expired:
            sub.status = 'expired'
            sub.save(update_fields=['status'])

    print(f"Expired {count} subscriptions")



from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import requests

from .models import Subscription, SubscriptionInvoice, Payment, PlanPrice


@shared_task
def auto_renew_subscriptions():

    soon_expire = timezone.now() + timedelta(days=1)

    subs = Subscription.objects.filter(
        is_auto_renew=True,
        end_date__lte=soon_expire,
        status='active',
        zarinpal_token__isnull=False
    )

    for sub in subs:

        try:
            renew_subscription_payment(sub)

        except Exception as e:
            print("Auto renew failed:", e)


from celery import shared_task
from subscription.models import Subscription
from django.utils import timezone
from datetime import timedelta


@shared_task
def handle_payment_paid_event(event_data):

    subscription = Subscription.objects.get(
        id=event_data["subscription_id"]
    )

    # مثال Notification
    try:
        from telbot.services import TelegramNotifier

        TelegramNotifier.send_payment_success(subscription)

    except:
        pass


import redis
import json

redis_client = redis.Redis()


def start_payment_listener():

    pubsub = redis_client.pubsub()
    pubsub.subscribe("events:payment_paid")

    for message in pubsub.listen():

        if message["type"] != "message":
            continue

        data = json.loads(message["data"])

        handle_payment_paid_event.delay(data)
