from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from datetime import timedelta
from .models import Plan, PlanPrice, Subscription, SubscriptionInvoice
from .serializers import PlanSerializer, SubscriptionSerializer
from rest_framework import viewsets
from rest_framework.decorators import action
from payments.services.payment_service import PaymentService
from django.contrib.contenttypes.models import ContentType

class PlanListAPIView(generics.ListAPIView):
    queryset = Plan.objects.filter(is_active=True).prefetch_related("features", "prices")
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]


class CurrentSubscriptionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        store = request.user.profile.store

        try:
            subscription = store.subscription
        except Subscription.DoesNotExist:
            return Response({"detail": "No subscription"}, status=404)

        serializer = SubscriptionSerializer(subscription)
        return Response(serializer.data)


class CreateInvoiceAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        plan_id = request.data.get("plan_id")
        months = request.data.get("months")

        store = request.user.profile.store

        plan_price = PlanPrice.objects.get(
            plan_id=plan_id,
            months=months,
            is_active=True
        )

        invoice = SubscriptionInvoice.objects.create(
            subscription=store.subscription,
            plan_price=plan_price,
            amount=plan_price.price
        )

        return Response({
            "invoice_id": invoice.id,
            "amount": invoice.amount
        })


from subscription.services.throttles import PlanThrottle

class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Plan.objects.filter(is_active=True)\
        .prefetch_related("features__feature", "prices")

    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [PlanThrottle]





class SubscriptionViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=["get"])
    def current(self, request):
        store = request.user.profile.store

        try:
            subscription = store.subscription
        except Subscription.DoesNotExist:
            return Response({"detail": "No subscription"}, status=404)

        serializer = SubscriptionSerializer(subscription)
        return Response(serializer.data)


from rest_framework import status
from .models import PlanPrice, SubscriptionInvoice
from rest_framework.permissions import AllowAny
from subscription.services.throttles import CreateInvoiceThrottle

class SubscriptionActionViewSet(viewsets.ViewSet):

    permission_classes = [AllowAny]
    throttle_classes = [CreateInvoiceThrottle]

    @action(detail=False, methods=["post"])
    def create_invoice(self, request):

        from products.models import Store
        from accounts.models import ProfileModel
        from django.db import transaction

        plan_id = request.data.get("plan_id")
        months = request.data.get("months")
        tel_id = request.data.get("tel_id")

        if not all([plan_id, months, tel_id]):
            return Response({"error": "Invalid parameters"}, status=400)

        try:
            profile = ProfileModel.objects.get(tel_id=tel_id)
        except ProfileModel.DoesNotExist:
            return Response({"error": "Profile not found"}, status=404)

        try:
            store = Store.objects.select_related("subscription").get(owner=profile)
        except Store.DoesNotExist:
            return Response({"error": "Store not found"}, status=404)

        with transaction.atomic():

            plan_price = PlanPrice.objects.select_for_update().filter(
                plan_id=plan_id,
                months=months,
                is_active=True
            ).first()

            if not plan_price:
                return Response({"error": "Invalid plan price"}, status=400)

            try:
                subscription = store.subscription
            except Subscription.DoesNotExist:
                return Response({"error": "Subscription not found"}, status=404)

            invoice = SubscriptionInvoice.objects.filter(
                subscription=subscription,
                plan_price=plan_price,
                status="created"
            ).first()

            if not invoice:
                invoice = SubscriptionInvoice.objects.create(
                    subscription=subscription,
                    plan_price=plan_price,
                    amount=plan_price.price,
                    status="created"
                )

            intent = invoice.payment_intent

            need_new_intent = False

            if not intent:
                need_new_intent = True

            elif intent.is_expired:
                intent.mark_expired()
                need_new_intent = True

            elif intent.status in ("failed", "canceled", "expired"):
                need_new_intent = True

            if need_new_intent:
                result = PaymentService.create_payment(
                    profile=profile,
                    amount=invoice.amount,
                    target=invoice,
                    country_iso="IR",
                    ip=request.META.get("REMOTE_ADDR"),
                    metadata={
                        "invoice_id": invoice.id
                    }
                )

                intent = result["intent"]

                invoice.payment_intent = intent
                invoice.save(update_fields=["payment_intent"])

                payment_url = result.get("payment_url")

            else:
                payment_url = intent.metadata.get("payment_url")

        return Response({
            "invoice_id": invoice.id,
            "amount": float(invoice.amount),
            "payment_url": payment_url
        }, status=status.HTTP_201_CREATED)

