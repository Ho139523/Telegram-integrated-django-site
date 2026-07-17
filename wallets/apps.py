# wallets/apps.py

from django.apps import AppConfig


class WalletsConfig(AppConfig):

    default_auto_field = "django.db.models.BigAutoField"

    name = "wallets"

    def ready(self):

        #
        # Django Signals
        #
        import wallets.signals

        #
        # Register Event Handlers
        #
        import wallets.events.handlers
