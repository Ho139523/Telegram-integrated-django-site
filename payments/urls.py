from django.urls import path
from payments.views import zarinpal_callback

urlpatterns = [
    path("callback/zarinpal/", zarinpal_callback, name="zarinpal_callback"),
]
