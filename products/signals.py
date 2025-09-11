from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Category


@receiver(post_save, sender=Category)
def update_subcategories_status(sender, instance, **kwargs):
    """
    سیگنال برای به‌روزرسانی وضعیت تمام زیردسته‌های یک دسته‌بندی
    وقتی وضعیت دسته‌بندی والد به False تغییر کند.
    """
    if not instance.status:  # اگر وضعیت دسته‌بندی False باشد
        subcategories = instance.get_all_subcategories()  # دریافت تمام زیردسته‌های
        for subcategory in subcategories:
            subcategory.status = False  # وضعیت زیردسته‌ها را به False تغییر دهید
            subcategory.save()  # ذخیره تغییرات
            
            
            
import requests
from products.models import Product, ProductAttribute, ProductImage
from utils.variables.TOKEN import TOKEN  # توکن ربات تلگرام شما
from telebot import TeleBot, types
from utils.telbot.functions import ProductHandler  # ایمپورت تابع ارسال محصول
from telbot.sessions import CartSessionManager, RedisStateManager
from telbot.sessions import session_manager


app = TeleBot(token=TOKEN)  # ایجاد شیء ربات تلگرام

# @receiver(post_save, sender=Product)
# def send_product_to_channel(sender, instance, created, **kwargs):
#     """
#     وقتی محصول جدید ساخته شد، پیامش به کانال مربوط به فروشگاه ارسال شود.
#     زیر پیام هم دکمه شیشه‌ای "همین حالا بخرش" اضافه می‌شود.
#     """
#     if created:
#         try:
#             current_site = "https://intelleum.ir"

#             # کانال فروشگاه مربوطه
#             channel_id = instance.store.tel_channel  
#             if not channel_id:
#                 print(f"⚠ کانال برای فروشگاه {instance.store.name} تعریف نشده.")
#                 return

#             # ارسال پیام محصول
#             product_handler = ProductHandler(app, instance, current_site)
#             # session = session_manager.get_user_session(instance.tel_id, "product_message")
#             # session['channel_inline_buttons'] = True
#             # session_manager.set_user_session(instance.tel_id, session, "product_message")
#             product_handler.send_product_channel(channel_id)

#         except Exception as e:
#             print(f"⚠ خطا در ارسال محصول به کانال {instance.store.name}: {e}")



import asyncio
from telethon import TelegramClient
from django.db.models.signals import post_save
from django.dispatch import receiver
from products.models import Product
from utils.telbot.functions import ProductHandler
from telbot.views import current_site
from utils.variables.TOKEN import TOKEN, api_id, api_hash


# signals.py
import asyncio
import traceback
from telethon import TelegramClient, errors
from telethon.sessions import StringSession
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from products.models import Product

# signals.py
import asyncio
import traceback
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from telethon import TelegramClient
from telethon.sessions import StringSession
from products.models import Product
from utils.telbot.functions import ProductHandler  # همین کلاسی که متد send_product_channel دارد
from telethon.tl.types import InputMediaPhoto
# from telethon.tl.functions.messages import SendMedia



session_string = settings.TG_SESSION_STRING


from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from telethon import TelegramClient, Button
from telethon.sessions import StringSession
import asyncio, traceback
from products.models import Product
from utils.telbot.functions import ProductHandler  # کلاس شما
from django.conf import settings
# فقط برای ذخیره id محصول جدید

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=ProductImage)
def send_album_when_all_images_added(sender, instance, created, **kwargs):
    if not created:
        return

    product = instance.product

    # کل تصاویر فعلی به همراه تصویر اصلی
    total_images = [product.main_image.path] + [img.image.path for img in product.images.all()]

    # فرض می‌کنیم تعداد کل عکس‌ها همیشه 4 است
    if len(total_images) == 4:
        print("✅ همه عکس‌ها اضافه شدند. آماده ارسال آلبوم!")

        async def _send():
            client = TelegramClient(
                StringSession(settings.TG_SESSION_STRING),
                api_id,
                api_hash
            )
            await client.connect()
            if not await client.is_user_authorized():
                print("⚠ Session معتبر نیست.")
                return

            handler = ProductHandler(client, product, current_site, photos=total_images)
            await handler.send_product_channel(product.store.tel_channel, buttons=True)
            await client.disconnect()

        import asyncio
        asyncio.run(_send())

