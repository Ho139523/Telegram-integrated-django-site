from .start import router as start_router
from .product import register_admin_handlers
from aiobot.handlers.join_check import router as subscription_router

def register_all_handlers(dp):
    """
    تمام Routerها و هندلرهای ساده را در Dispatcher ثبت می‌کند.
    """
    # اضافه کردن Routerها (سبک جدید aiogram 3.x)
    dp.include_router(start_router)
    # اگر subscription_router داری:
    dp.include_router(subscription_router)
    # ثبت هندلرهایی که با تابع جداگانه رجیستر می‌شوند
    register_admin_handlers(dp)
