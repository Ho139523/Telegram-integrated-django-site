from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from payments.models.attempt import PaymentAttempt
from payments.gateways.zarinpal import ZarinPalGateway


def zarinpal_callback(request):

    authority = request.GET.get("Authority")
    status = request.GET.get("Status")

    attempt = get_object_or_404(PaymentAttempt, authority=authority)

    gateway = ZarinPalGateway()
    result = gateway.verify_payment(attempt, status)

    if result:
        return HttpResponse("Payment Successful ✅")

    return HttpResponse("Payment Failed ❌")
