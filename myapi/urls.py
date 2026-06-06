from django.urls import path, include

# Heart API
from .views import HeartCreateAPIView, CheckTelegramUserRegistrationView



urlpatterns = [
    # Heart API
    path("heartrecords/", HeartCreateAPIView.as_view()),
]


# accounts
from myapi.products.views import *
from myapi.accounts.views import *
from myapi.payment.views import *
from myapi.subscription.views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r"stores", StoreViewSet)
router.register(r"products", ProductViewSet)
router.register(r"profiles", ProfileViewSet)
router.register(r"carts", CartViewSet)
router.register(r"cartitems", CartItemViewSet)
router.register(r"productvariants", ProductVariantViewSet)
router.register(r"productoptions", ProductOptionViewSet)
router.register(r"productoptionvalues", ProductOptionValueViewSet)
router.register(r"plans", PlanViewSet)


urlpatterns += [
    path('', include(router.urls))
]

# urlpatterns += [
#     path('persons/', PersonList.as_view(), name='person_list'),
#     path('persons/<int:pk>/', PersonDetail.as_view(), name='person_detail'),
#     path('books/', BookList.as_view(), name='book_list'),
#     path('books/<int:pk>/', BookDetail.as_view(), name='book_detail'),
# ]

