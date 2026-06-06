from rest_framework import viewsets
from myapi.subscription.PlanSerializerFile import PlanSerializer
from subscription.models import Plan
from rest_framework.permissions import AllowAny


class PlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.filter(is_active=True).prefetch_related("features", "prices")
    serializer_class = PlanSerializer
    permission_classes = [AllowAny]

