# payment/views/refund.py

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from payment.models import Transaction
from payment.services.refund_service import refund_transaction


@csrf_exempt
def refund_payment(request, transaction_id):

    if request.method != "POST":
        return JsonResponse(
            {
                "error": "Method not allowed"
            },
            status=405,
        )

    try:

        transaction = Transaction.objects.get(
            id=transaction_id,
        )

    except Transaction.DoesNotExist:

        return JsonResponse(
            {
                "error": "Transaction not found"
            },
            status=404,
        )

    try:

        refund_transaction(
            transaction=transaction,
        )

        return JsonResponse(
            {
                "success": True,
                "message": "Refund completed successfully."
            }
        )

    except Exception as exc:

        return JsonResponse(
            {
                "success": False,
                "error": str(exc),
            },
            status=400,
        )
