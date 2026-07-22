from payment.models import Transaction


def get_transaction_by_authority(authority):

    return Transaction.objects.get(
        authority=authority,
    )
