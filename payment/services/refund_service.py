# payment/services/refund_service.py

from django.db import transaction


@transaction.atomic
def refund_transaction(*, transaction):

    transaction.refund()

    return transaction
