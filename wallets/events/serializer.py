# wallets/events/serializer.py

from dataclasses import asdict, is_dataclass
from decimal import Decimal
from datetime import date, datetime
from enum import Enum
from uuid import UUID


def _encode(value):

    if isinstance(value, Decimal):
        return {
            "__type__": "Decimal",
            "value": str(value),
        }

    if isinstance(value, UUID):
        return {
            "__type__": "UUID",
            "value": str(value),
        }

    if isinstance(value, datetime):
        return {
            "__type__": "datetime",
            "value": value.isoformat(),
        }

    if isinstance(value, date):
        return {
            "__type__": "date",
            "value": value.isoformat(),
        }

    if isinstance(value, Enum):
        return {
            "__type__": "Enum",
            "value": value.value,
        }

    if isinstance(value, dict):
        return {
            k: _encode(v)
            for k, v in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            _encode(v)
            for v in value
        ]

    return value


def serialize(event):

    if not is_dataclass(event):
        raise TypeError("Event must be dataclass.")

    return {
        "event_type": event.__class__.__name__,
        "payload": _encode(asdict(event)),
    }
