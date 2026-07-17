# wallets/services/decorators.py

from functools import wraps

from wallets.services.idempotency import (
    get_cached_result,
    save_result,
)


def idempotent(service):

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):

            key = kwargs.get("operation_id")

            cached = get_cached_result(
                key=key,
                service=service,
            )

            if cached:
                return cached

            obj = func(*args, **kwargs)

            return save_result(
                key=key,
                service=service,
                obj=obj,
            )

        return wrapper

    return decorator
