# wallets/events/base.py

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


@dataclass(
    slots=True,
    frozen=True,
)
class DomainEvent:

    event_id: str = field(
        default_factory=lambda: str(uuid4()),
        init=False,
    )

    occurred_at: datetime = field(
        default_factory=datetime.utcnow,
        init=False,
    )
