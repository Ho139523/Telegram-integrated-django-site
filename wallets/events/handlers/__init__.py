"""
Import every handler module.

Simply importing these modules causes
their @handles(...) decorators to run,
which automatically registers handlers.
"""

from .accounting import AccountingHandler
from .analytics import AnalyticsHandler
from .audit import AuditHandler
from .notifications import NotificationHandler
from .webhooks import WebhookHandler

__all__ = [
    "AccountingHandler",
    "AnalyticsHandler",
    "AuditHandler",
    "NotificationHandler",
    "WebhookHandler",
    ]
