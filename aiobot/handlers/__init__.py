# aiobot/handlers/__init__.py

# ایمپورت Routerها از فایل‌های مختلف
from .start import router as start_router
from .product import register_admin_handlers
# اگر فایل هندلر دیگری داری، اینجا ایمپورت و اضافه کن
# from .subscription import router as subscription_router

def register_all_handlers(dp):
    """
    تمام Routerها و هندلرهای ساده را در Dispatcher ثبت می‌کند.
    """
    # اضافه کردن Routerها (سبک جدید aiogram 3.x)
    dp.include_router(start_router)
    # اگر subscription_router داری:
    # dp.include_router(subscription_router)

    # ثبت هندلرهایی که با تابع جداگانه رجیستر می‌شوند
    register_admin_handlers(dp)
