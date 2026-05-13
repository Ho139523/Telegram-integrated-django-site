# =============================
# Imports
# =============================

from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from utils.funcs.django_social_redirect import custom_complete
from ai_chat.views import GenerateResponse

# Accounts
from accounts.views import UserViewSet, ProfileViewSet, AddressViewSet, me

# Products
from products.views import (
    StoreViewSet,
    UnitViewSet,
    CategoryViewSet,
    ProductViewSet,
    ProductImageViewSet,
    ProductAttributeViewSet,
    ProductVariantViewSet,
    ProductOptionViewSet,
    ProductOptionValueViewSet,
)

# Payment
from payment.views import (
    CartViewSet,
    CartItemViewSet,
    TransactionViewSet,
    SplitPaymentViewSet,
    SaleViewSet,
)

# Telegram Bot
from telbot.views import (
    ConversationViewSet,
    MessageViewSet,
    CachedMediaViewSet,
)

# Subscription
from subscription.views import (
    PlanViewSet,
    SubscriptionViewSet,
    SubscriptionActionViewSet,
)

from accounts.views import BotProfileViewSet

# =============================
# Router Configuration
# =============================

router = DefaultRouter()
bot_router = DefaultRouter()


# Accounts
router.register(r'users', UserViewSet)
router.register(r'profiles', ProfileViewSet, basename='profile')
router.register(r'addresses', AddressViewSet)

# Products
router.register(r'stores', StoreViewSet, basename='store')
router.register(r'units', UnitViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet, basename='product')
router.register(r'product-images', ProductImageViewSet)
router.register(r'product-attributes', ProductAttributeViewSet)
router.register(r'product-variants', ProductVariantViewSet)
router.register(r'product-options', ProductOptionViewSet)
router.register(r'product-option-values', ProductOptionValueViewSet)

# Payment
router.register(r'carts', CartViewSet, basename='cart')
router.register(r'cart-items', CartItemViewSet)
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'split-payments', SplitPaymentViewSet)
router.register(r'sales', SaleViewSet)

# Telegram Bot
router.register(r'conversations', ConversationViewSet)
router.register(r'messages', MessageViewSet)
router.register(r'cached-media', CachedMediaViewSet)

# Subscription
router.register(r'plans', PlanViewSet, basename='plan')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(
    r'subscription-actions',
    SubscriptionActionViewSet,
    basename='subscription-actions'
)


bot_router.register(r'profiles', BotProfileViewSet, basename='bot-profile')

# =============================
# URL Patterns
# =============================

urlpatterns = [

    # Admin
    path('admin/', admin.site.urls),

    # Main pages
    path('', include('mainpage.urls')),

    # API Router
    path('api/', include(router.urls)),

    path('api/bot/', include(bot_router.urls)),

    # Authentication
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/me/', me, name='me'),

    # Apps
    path('cv/', include('cv.urls', namespace='cv')),
    path('heartpred/', include('heartpred.urls', namespace='heartpred')),
    path('accounts/', include('accounts.urls')),
    path('socials/', include('social_django.urls', namespace='social')),

    path(
        'socials/complete/google-oauth2/',
        custom_complete,
        name="custom_complete"
    ),

    path('telbot/', include('telbot.urls', namespace='telbot')),
    path('balebot/', include('balebot.urls', namespace='balebot')),

    path('', include('payment.urls')),

    # AI
    path('generate/', GenerateResponse.as_view(), name='generate-response'),

]

# =============================
# Static / Media
# =============================

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
