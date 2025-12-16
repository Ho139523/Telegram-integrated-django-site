from celery import shared_task
from django.utils import timezone
from datetime import timedelta

@shared_task
def mark_expired_transactions():
    from payment.models import Transaction  # <-- moved here
    """Mark transactions pending for more than 1 hour as failed"""
    one_hour_ago = timezone.now() - timedelta(hours=1)
    expired_txns = Transaction.objects.filter(status="pending", created_at__lt=one_hour_ago)
    count = expired_txns.count()
    expired_txns.update(status="failed")
    return f"{count} transactions marked as failed"

@shared_task
def send_payment_notifications_task(transaction_id):
    from payment.models import Transaction  # <-- moved here
    from payment.views import send_payment_notifications  # <-- also local import
    txn = Transaction.objects.get(id=transaction_id)
    sales = list(txn.sales.all())
    send_payment_notifications(txn, sales)
