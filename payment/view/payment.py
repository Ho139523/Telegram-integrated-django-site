from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from payment.selectors.transaction import (
    get_transaction_by_authority
)

from payment.services.checkout_service import (
    CheckoutService
)

from payment.services.verify_service import (
    VerifyService
)


def send_request(request):

    if request.method != "GET":

        return JsonResponse(
            {
                "error": "Method not allowed"
            },
            status=405
        )

    payment_id = request.GET.get("pid")

    if not payment_id:

        return JsonResponse(
            {
                "error": "شناسه پرداخت نامعتبر است"
            },
            status=400
        )

    try:

        service = CheckoutService()

        result = service.create_payment(
            payment_id=payment_id
        )

        return result

    except Exception as exc:

        return JsonResponse(
            {
                "error": str(exc)
            },
            status=500
        )


@csrf_exempt
def verify(request):

    authority = request.GET.get(
        "Authority"
    )

    status = request.GET.get(
        "Status"
    )

    if not authority:

        return JsonResponse(
            {
                "error": "Missing authority"
            },
            status=400
        )

    try:

        transaction = (
            get_transaction_by_authority(
                authority
            )
        )

    except Exception:

        return JsonResponse(
            {
                "error": "Transaction not found"
            },
            status=404
        )

    try:

        service = VerifyService()

        result = service.process(
            transaction=transaction,
            status=status
        )

        return render(
            request,
            result["template"],
            result["context"]
        )

    except Exception as exc:

        return JsonResponse(
            {
                "error": str(exc)
            },
            status=500
        )
