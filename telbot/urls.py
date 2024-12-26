from django.urls import path
from .views import TelegramBotWebhookView
from myapi.views import CheckTelegramUserRegistrationView, telegram_activation_redirect

app_name = 'telbot'

urlpatterns = [
    path('webhook/', TelegramBotWebhookView.as_view(), name='telegram_webhook'),
    
    # check telegram registration
    path('api/check-registration/', CheckTelegramUserRegistrationView.as_view(), name='check-registration'),
    
    # account acctivation
    path('activate/telegram/<uidb64>/<token>/', telegram_activation_redirect, name='telegram_activate'),

]