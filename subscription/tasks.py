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

