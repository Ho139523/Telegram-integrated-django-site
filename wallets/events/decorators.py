from wallets.events.registry import registry


def handles(
    *event_types,
):
    """
    Register a handler for one or more events.

    Example:

        @handles(
            DepositCreated,
            RefundCreated,
        )
        class AccountingHandler(...)
    """

    def decorator(handler_cls):

        handler_cls.handles = tuple(
            event_types
        )

        registry.register(
            handler_cls()
        )

        return handler_cls

    return decorator
