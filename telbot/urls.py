from django.urls import path
from .views import TelegramBotWebhookView
from myapi.views import CheckTelegramUserRegistrationView

app_name = 'telbot'

urlpatterns = [
    path('webhook/', TelegramBotWebhookView.as_view(), name='telegram_webhook'),
    
    # check telegram registration
    path('api/check-registration/', CheckTelegramUserRegistrationView.as_view(), name='check-registration'),
]