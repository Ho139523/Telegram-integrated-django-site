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
