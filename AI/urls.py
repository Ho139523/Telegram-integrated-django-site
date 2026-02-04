from django.urls import URLPattern, URLResolver

def add_port_to_reverse_output():
    from rest_framework.reverse import reverse
    from urllib.parse import urlparse, urlunparse

    original_reverse = reverse

    def custom_reverse(*args, **kwargs):
        url = original_reverse(*args, **kwargs)
        parsed = urlparse(url)
        if parsed.port is None:
            parsed = parsed._replace(netloc=f"{parsed.hostname}:8443")
        return urlunparse(parsed)

    import rest_framework.reverse
    rest_framework.reverse.reverse = custom_reverse

add_port_to_reverse_output()


from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from utils.funcs.django_social_redirect import custom_complete

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('mainpage.urls')),  # OK if it needs the root path
    path('apim/', include('myapi.urls')),
    path('cv/', include('cv.urls', namespace='cv')),  # Use a distinct prefix
    path('heartpred/', include('heartpred.urls', namespace='heartpred')),  # Use a distinct prefix
    path('accounts/', include('accounts.urls')),
    path('socials/', include('social_django.urls', namespace='social')),
    path('socials/complete/google-oauth2/', custom_complete, name="custom_complete"),
    path('telbot/', include('telbot.urls', namespace='telbot')),  # Prefix `telbot` instead of empty ''
    path('', include('payment.urls')),
]


########################## SERIALIZERS #######################

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from accounts.views import UserViewSet, ProfileViewSet, AddressViewSet, me
from products.views import (
    StoreViewSet, UnitViewSet, CategoryViewSet, ProductViewSet,
    ProductImageViewSet, ProductAttributeViewSet, ProductVariantViewSet,
    ProductOptionViewSet, ProductOptionValueViewSet
)
from payment.views import CartViewSet, CartItemViewSet, TransactionViewSet, SplitPaymentViewSet, SaleViewSet
from telbot.views import ConversationViewSet, MessageViewSet, CachedMediaViewSet
from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


router = DefaultRouter()

# accounts
router.register(r'users', UserViewSet)
router.register(r'profiles', ProfileViewSet, basename='profile')
router.register(r'addresses', AddressViewSet)

# products
router.register(r'stores', StoreViewSet, basename='store')
router.register(r'units', UnitViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet, basename='product')
router.register(r'product-images', ProductImageViewSet)
router.register(r'product-attributes', ProductAttributeViewSet)
router.register(r'product-variants', ProductVariantViewSet)
router.register(r'product-options', ProductOptionViewSet)
router.register(r'product-option-values', ProductOptionValueViewSet)

# payment
router.register(r'carts', CartViewSet, basename='cart')
router.register(r'cart-items', CartItemViewSet)
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'split-payments', SplitPaymentViewSet)
router.register(r'sales', SaleViewSet)

# telbot
router.register(r'conversations', ConversationViewSet)
router.register(r'messages', MessageViewSet)
router.register(r'cached-media', CachedMediaViewSet)


urlpatterns += [
    path('api/', include(router.urls)),
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/me/', me, name='me')
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



from ai_chat.views import GenerateResponse

urlpatterns += [
    path('generate/', GenerateResponse.as_view(), name='generate-response'),
]

