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
from telebot import TeleBot
from utils.telbot.functions import ProductHandler  # ایمپورت تابع ارسال محصول


app = TeleBot(token=TOKEN)  # ایجاد شیء ربات تلگرام
CHANNEL_ID = "@your_channel_username"  # آی‌دی کانال یا مقدار عددی مثل -1001234567890

@receiver(post_save, sender=Product)
def send_product_to_channel(sender, instance, created, **kwargs):
    """
    این تابع هنگام اضافه شدن محصول جدید به دیتابیس اجرا شده و آن را به کانال ارسال می‌کند.
    """
    if created:  # فقط وقتی محصول جدید اضافه شد اجرا شود
        try:
            current_site = f"https://intelleum.ir"  # دریافت دامنه سایت
            # send_product_message(app, message=None, product=instance, current_site=current_site, buttons=False, channel_id=-1002299397356)
            product_handler = ProductHandler(app, instance, current_site)
            product_handler.send_product_message(chat_id)
        except Exception as e:
            print(f"⚠ خطا در ارسال محصول به کانال: {e}")

