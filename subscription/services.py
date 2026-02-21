from django.utils import timezone
from subscription.models import Subscription

def cleanup_expired_subscriptions():
    now = timezone.now()

    Subscription.objects.filter(
        status__in=['trial', 'active'],
        end_date__lt=now
    ).update(status='expired')
