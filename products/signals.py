import asyncio
import traceback
import time

import attr
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from asgiref.sync import sync_to_async

import telebot_router
from telethon import TelegramClient
from telethon.sessions import StringSession
from telebot import TeleBot, types

from products.models import Product, ProductImage, Category, ProductVariant
from accounts.models import ProfileModel
from utils.telbot.functions import ProductHandler, t
from utils.variables.TOKEN import TOKEN, api_id, api_hash, BOT_ID
from utils.variables.translate import translations

from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from django.db.models.signals import post_delete
from AI.settings import SITE_DOMAIN

# --- CONFIG ---
API_ID = api_id
API_HASH = api_hash
SESSION_STRING = settings.TG_SESSION_STRING
BOT_TOKEN = TOKEN

bot = TeleBot(BOT_TOKEN)


# --- Translation Helper ---
def helper(product):
    """
    دریافت tel_id و lang صاحب فروشگاه به صورت sync_to_async
    """
    store = product.store
    chat_id = store.owner.tel_id

    return store.lang, store.id, product.code, chat_id


async def translate(lang, key, **kwargs):
    """
    تابع ترجمه‌ی متن با توجه به زبان کاربر
    """
    try:
        text = translations.get(key, {}).get(lang, translations[key]["en"])
        if kwargs:
            text = text.format(**kwargs)
        return text
    except Exception as e:
        print(f"⚠ Translation error for key '{key}': {e}")
        return translations.get(key, {}).get("en", key)


# --- Signal: Category status cascade ---
@receiver(post_save, sender=Category)
def update_subcategories_status(sender, instance, **kwargs):
    """
    وقتی دسته‌بندی غیر فعال شود، تمام زیردسته‌های آن هم غیر فعال می‌شوند
    """
    if not instance.status:
        subcategories = instance.get_all_subcategories()
        for subcategory in subcategories:
            subcategory.status = False
            subcategory.save()

    if instance.status:
        subcategories = instance.get_all_subcategories()
        for subcategory in subcategories:
            subcategory.status = True
            subcategory.save()


# --- Async Telegram Sending ---
def send_album_and_button(channel_id, product, photos, attributes):
    """
    آلبوم محصول را با Telethon می‌فرستد و سپس دکمه Buy Now را با TeleBot ارسال می‌کند
    """
    try:

        # --- 1. واکشی اطلاعات صاحب فروشگاه ---
        owner_lang, store_id, product_id, chat_id = helper(product)
        buyer_lang = ProfileModel.objects.get(tel_id=chat_id).lang


        # --- 2. ارسال آلبوم ---
        handler = ProductHandler(bot, product, SITE_DOMAIN, photos=photos, attributes=attributes, chat_id=chat_id)
        handler.send_product_message(channel_id, buttons=False)


        # --- 3. ترجمه‌ی متن دکمه ---
        buy_now_text = t("message", "buy_now", chat_id=chat_id)

        # --- 4. ارسال دکمه با TeleBot ---
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton( buy_now_text, url=f"{SITE_DOMAIN}/pay/telegrambot/?start=store_{store_id}_product_{product_id}_lang_{buyer_lang}" ))


        bot.send_message(channel_id, "👇👇👇👇👇👇👇👇👇", reply_markup=markup)

    except Exception as e:
        print(f"⚠ Error in send_album_and_button:{traceback.format_exc()}")



@receiver(post_save, sender=ProductImage)
def send_album_when_all_images_added(sender, instance, created, **kwargs):
    """
    وقتی همه‌ی تصاویر محصول (از جمله main_image) اضافه شدند،
    آلبوم به کانال ارسال شود.
    """

    if not created:
        return

    product = instance.product

    # ⚡ اینجا ORM را در محیط sync اجرا و list می‌کنیم (مهم!)
    attributes = list(product.attributes.all())

    # جمع‌آوری همه عکس‌ها
    photos = []
    if product.main_image:
        photos.append(product.main_image.path)
    photos += [img.image.path for img in product.images.all()]

    # فرض: فقط وقتی تعداد عکس‌ها 4 تا شد ارسال کنیم
    if len(photos) == 4:

        channel_id = product.store.tel_channel
        if not channel_id:
            print(f"⚠ No Telegram channel defined for store {product.store.name}")
            return

        # اینجا attributes به‌صورت list پاس داده می‌شود ✅
        send_album_and_button(channel_id, product, photos, attributes)


# سیگنال برای زمانیکه values به واریانت اضافه شد — اگر SKU خالی باشد آن را تولید می‌کند.
@receiver(m2m_changed, sender=ProductVariant.values.through)
def productvariant_values_changed(sender, instance, action, pk_set, **kwargs):
    # action می‌تواند 'post_add' ، 'post_remove' و ... باشد
    if action == "post_add" or action == "post_clear":
        # اگر values الان وجود دارد و sku خالیه، تولید کن
        try:
            if instance.values.exists() and not instance.sku:
                instance.ensure_sku(save_if_missing=True)
        except Exception:
            # لاگ خطا در صورت نیاز
            pass



# @receiver(post_save, sender=ProductVariant)
# def update_product_stock_on_variant_save(sender, instance, **kwargs):
#     product = instance.product
#     product.sync_stock()
#     product.save(update_fields=["stock"])


# @receiver(post_delete, sender=ProductVariant)
# def update_product_stock_on_variant_delete(sender, instance, **kwargs):
#     product = instance.product
#     product.sync_stock()
#     product.save(update_fields=["stock"])




