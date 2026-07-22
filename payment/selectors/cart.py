from payment.models import Cart


def get_cart(profile):

    return Cart.objects.get(
        profile=profile,
    )
