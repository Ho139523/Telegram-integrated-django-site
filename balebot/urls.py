from django.urls import path
#from aiobot.webhook import BaleBotWebhookView
from balebot.views import BaleBotWebhookView
#from myapi.views import CheckBaleUserRegistrationView

app_name = 'balebot'

urlpatterns = [
    path('webhook/', BaleBotWebhookView.as_view(), name='bale_webhook'),
    
    # check bale registration
    #path('api/check-registration/', CheckBaleUserRegistrationView.as_view(), name='check-registration'),
    
]
