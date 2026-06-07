from celery import shared_task
from django.utils import timezone
from django.db import transaction
from datetime import timedelta

from .models import Subscription, SubscriptionInvoice


# =========================================================
# 1. Expire subscriptions
# =========================================================
@shared_task
def expire_subscriptions():
    """
    پایان دادن به اشتراک‌های منقضی شده
    """
    now = timezone.now()

    with transaction.atomic():
        expired_qs = Subscription.objects.select_for_update().filter(
            end_date__lte=now,
            status='active'
        )

        count = expired_qs.count()

        expired_qs.update(status='expired')

    return f"Expired {count} subscriptions"


# =========================================================
# 2. Auto renew subscriptions (trigger payment)
# =========================================================
@shared_task
def auto_renew_subscriptions():
    """
    پیدا کردن اشتراک‌هایی که نزدیک انقضا هستند
    و ارسال برای پرداخت جدید
    """

    from .services import renew_subscription_payment  # فرض: شما این سرویس را داری

    soon_expire = timezone.now() + timedelta(days=1)

    subs = Subscription.objects.filter(
        is_auto_renew=True,
        end_date__lte=soon_expire,
        status='active',
        zarinpal_token__isnull=False
    ).only("id")

    for sub in subs:
        try:
            # بهتر: async
            renew_subscription_payment.delay(sub.id)

        except Exception as e:
            print(f"[AUTO_RENEW_ERROR] subscription={sub.id} error={e}")

    return f"Queued {subs.count()} subscriptions for renewal"


# =========================================================
# 3. Handle payment success event
# =========================================================
@shared_task
def handle_payment_paid_event(event_data):
    """
    وقتی پرداخت موفق شد (از webhook یا queue)
    """

    from .models import Subscription
    from telbot.services import TelegramNotifier

    try:
        subscription = Subscription.objects.get(
            id=event_data["subscription_id"]
        )

        # مثال: فعال‌سازی یا تمدید
        subscription.status = "active"
        subscription.save(update_fields=["status"])

        # نوتیفیکیشن
        try:
            TelegramNotifier.send_payment_success(subscription)
        except Exception:
            pass

        return f"Processed payment for subscription {subscription.id}"

    except Subscription.DoesNotExist:
        return "Subscription not found"


# =========================================================
# 4. Expire invoices (cleanup task)
# =========================================================
@shared_task
def expire_invoices():
    """
    فاکتورهای پرداخت نشده که قدیمی شده‌اند
    """

    now = timezone.now()

    expired = SubscriptionInvoice.objects.filter(
        status="created",
        created_at__lt=now - timedelta(hours=2)
    )

    count = expired.count()

    expired.update(status="expired")

    return f"Expired {count} invoices"