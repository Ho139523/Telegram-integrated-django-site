from django.urls import path
from .views import TelegramBotWebhookView, copy_text
from myapi.views import CheckTelegramUserRegistrationView

app_name = 'telbot'

urlpatterns = [
    path('webhook/', TelegramBotWebhookView.as_view(), name='telegram_webhook'),
    
    # check telegram registration
    path('api/check-registration/', CheckTelegramUserRegistrationView.as_view(), name='check-registration'),
    
    # Copy the text link
    path('copy-telegram-text-link/<slug:slug>/', copy_text, name='copy-text'),
]