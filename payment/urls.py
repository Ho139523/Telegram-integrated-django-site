from django.urls import path, re_path
from .views import *

app_name = 'payment'
urlpatterns = [
    path('buy/', send_request, name='request'),
    path('verify/', verify, name='verify'),
    path("verify-async/", async_verify_payment, name="verify-async"),
    path('pay/telegrambot/', TelegramBotRedirectView.as_view(), name='telegram_bot_redirect'),
]


