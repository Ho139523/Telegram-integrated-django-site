from django.urls import path
from .views import TelegramBotWebhookView

app_name='telbot'
urlpatterns = [
    path('webhook/', TelegramBotWebhookView.as_view(), name='telegram_webhook'),
]