class PaymentState:
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    EXPIRED = "expired"


class SubscriptionState:
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"