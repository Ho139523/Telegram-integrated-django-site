from django.urls import path, re_path
from .views import *

app_name = 'payment'
urlpatterns = [
    path('buy/', send_request, name='request'),
    path('verify/', verify, name='verify'),
    path("verify-async/", async_verify_payment, name="verify-async"),
]


