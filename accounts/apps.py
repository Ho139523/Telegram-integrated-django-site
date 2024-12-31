from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        import django.db.models.signals  # اطمینان از لود شدن سیگنال‌های اصلی
        from django.utils.module_loading import autodiscover_modules
        autodiscover_modules('signals')