# wallets/events/deserializer.py

from decimal import Decimal
from datetime import datetime, date
from uuid import UUID

from wallets.events.types import (
    DepositCreated,
    WithdrawalCreated,
    TransferCompleted,
    RefundCreated,
    HoldCreated,
    HoldReleased,
    SalePendingCreated,
    SaleReleased,
    SaleRefunded,
)


EVENTS = {
    cls.__name__: cls
    for cls in (
        DepositCreated,
        WithdrawalCreated,
        TransferCompleted,
        RefundCreated,
        HoldCreated,
        HoldReleased,
        SalePendingCreated,
        SaleReleased,
        SaleRefunded,
    )
}


def _decode(value):

    if isinstance(value, dict):

        if "__type__" in value:

            t = value["__type__"]

            if t == "Decimal":
                return Decimal(value["value"])

            if t == "UUID":
                return UUID(value["value"])

            if t == "datetime":
                return datetime.fromisoformat(value["value"])

            if t == "date":
                return date.fromisoformat(value["value"])

            return value["value"]

        return {
            k: _decode(v)
            for k, v in value.items()
        }

    if isinstance(value, list):
        return [
            _decode(v)
            for v in value
        ]

    return value


def deserialize(event_type, payload):

    cls = EVENTS[event_type]

    payload = _decode(payload)

    return cls(**payload)
