from dataclasses import dataclass

@dataclass
class PaymentEvent:
    invoice_id: int
    subscription_id: int
    status: str
