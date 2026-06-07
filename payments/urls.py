from django.urls import path
from payments.views import zarinpal_callback

urlpatterns = [
    path(
        "webhook/zarinpal/",
        zarinpal_callback,
        name="zarinpal-callback"
    ),
]