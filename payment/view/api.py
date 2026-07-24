from rest_framework import (
    viewsets,
    permissions,
)

from payment.models import (
    Cart,
    CartItem,
    Sale,
)

from payment.serializers import (
    CartSerializer,
    CartItemSerializer,
    SaleSerializer,
)


class CartViewSet(
    viewsets.ModelViewSet
):

    serializer_class = (
        CartSerializer
    )

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get_queryset(self):

        try:

            profile = (
                self.request.user.profilemodel
            )

            return Cart.objects.filter(
                profile=profile
            )

        except ProfileModel.DoesNotExist:

            return Cart.objects.none()

    def perform_create(
        self,
        serializer,
    ):

        serializer.save(
            profile=(
                self.request
                .user
                .profilemodel
            )
        )


class CartItemViewSet(
    viewsets.ModelViewSet
):

    queryset = CartItem.objects.all()

    serializer_class = (
        CartItemSerializer
    )

    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly
    ]


class SaleViewSet(
    viewsets.ModelViewSet
):

    queryset = Sale.objects.all()

    serializer_class = (
        SaleSerializer
    )

    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly
    ]
