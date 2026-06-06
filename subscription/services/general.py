# subscription/services.py

from subscription.models import Subscription, Plan
from django.utils import timezone
from datetime import timedelta


class SubscriptionService:

    @staticmethod
    def get_or_create_subscription(store):

        subscription = Subscription.objects.filter(
            store=store
        ).first()

        if subscription:
            return subscription

        basic_plan = Plan.objects.get(code="basic")

        return Subscription.objects.create(
            store=store,
            plan=basic_plan,
            status="trial",
            end_date=timezone.now() + timedelta(days=7)
        )