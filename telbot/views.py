# General imports
from math import prod
import re
import trace
from traceback import format_exc
from telebot import TeleBot, types
from collections import defaultdict
import requests
import random
from django.contrib.sites.shortcuts import get_current_site
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from django.utils.html import format_html
import os
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from django.conf import settings as sett
from datetime import datetime
from decouple import config
import pycountry

# support imports
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup
from telebot import custom_filters

# Variables imports
from utils.variables.TOKEN import TOKEN, BOT_ID
from utils.variables.CHANNELS import my_channels_with_atsign, my_channels_without_atsign
from utils.telbot.functions import *
from utils.telbot.functions import ProductHandler, SendCart, SendLocation, SendMarkup, t, AdvancedProductExporter
from utils.telbot.variables import customer_main_menu, extra_buttons, retun_menue, seller_main_menu, home_menu
from bs4 import BeautifulSoup

# import models
from products.models import Category, Product, ProductAttribute
from payment.models import Transaction
from telbot.models import ConversationModel, MessageModel
from telebot.types import Message

# copy telegram text link
from django.shortcuts import render

# signup
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from accounts.tokens import generate_token  # Update this with your token import
from django.utils import timezone
from datetime import timedelta
from accounts.models import ProfileModel, Address
from accounts.models import User
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.db.utils import IntegrityError
from django.db import transaction
from django.core.files.base import ContentFile

# functions and classes
from utils.telbot.functions import SubscriptionClass, CategoryClass

# python tools
from functools import wraps
from django.db.models.functions import Lower
from django.core.exceptions import ObjectDoesNotExist

###############################################################################################

# Logging setup
logger = logging.getLogger(__name__)

# support memmory
state_storage = StateMemoryStorage()

# App setup
app = TeleBot(token=TOKEN, state_storage=state_storage)
current_site = 'https://intelleum.ir:8443'

# subscription instance
subscription = SubscriptionClass(app)
subscription.register_handlers()

# Access shared user_sessions
from telbot.sessions import session_manager

# support class
chat_ids = []
texts = {}
codes = {}


class Support(StatesGroup):
    text = State()
    respond = State()
    code = State()


# model variables
main_menu = customer_main_menu
################################################################################################

# Webhook settings
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
import json
import logging

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class TelegramBotWebhookView(View):
    def post(self, request, *args, **kwargs):
        try:
            json_str = request.body.decode('UTF-8')
            logger.info(f"Received data: {json_str}")
            update = types.Update.de_json(json.loads(json_str))
            app.process_new_updates([update])
            return JsonResponse({"status": "success"}, status=200)
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=200)


#################################################################################################


def inject_main_menu(message):
    """
    A decorator-like function to determine and return the appropriate main menu for a user.
    """
    try:
        username = message.from_user.username
        # Get user profile and determine the menu
        profile = ProfileModel.objects.get(telegram=username)
        print(profile.user_level)
        if profile.user_level == ProfileModel.UserLevel.GREEN:
            return seller_main_menu
        else:
            return customer_main_menu
    except ProfileModel.DoesNotExist:
        # Default to customer menu if profile is not found
        return customer_main_menu
    except Exception as e:
        app.send_message(message.chat.id, f"خطا در دریافت اطلاعات منو: {e}")
        return customer_main_menu


# Function to escape all special characters with a backslash
def escape_special_characters(text):
    special_characters = r"([\*\_\[\]\(\)\~\`\>\#\+\-\=\|\{\}\.\!])"
    return re.sub(special_characters, r'\\\1', text)


def download_profile_photo(telegram_user_id, profile):
    try:
        # درخواست دریافت عکس پروفایل
        photos = app.get_user_profile_photos(telegram_user_id)

        if photos.total_count > 0:
            # دریافت file_id اولین عکس (آخرین عکس پروفایل)
            file_id = photos.photos[0][-1].file_id
            file_info = app.get_file(file_id)

            # لینک فایل
            file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"

            # دانلود عکس
            response = requests.get(file_url)

            if response.status_code == 200:
                # ساخت نام فایل
                file_name = f"registration/user_avatars/{telegram_user_id}.jpg"

                # ذخیره فایل به مدل پروفایل
                profile.avatar.save(file_name, ContentFile(response.content), save=True)

                return True
            else:
                print("Failed to download the profile photo.")
                return False
        else:
            print("User has no profile photo.")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def get_user_store(message):
    """Return the store belonging to the profile sending this message."""
    profile = ProfileModel.objects.get(tel_id=message.from_user.id)
    if not profile.seller_mode:
        return None
    try:
        return Store.objects.get(owner=profile)
    except Store.DoesNotExist:
        return None


####################################################################################################


@app.message_handler(func=lambda message: message.text.startswith("/start activate_"))
def handle_activation_account(message):
    try:
        parts = message.text.split('_')
        if len(parts) != 3:
            app.send_message(message.chat.id, "لینک فعالسازی نامعتبر است.")
            return

        _, uid, token = parts
        uid = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=uid)

        if generate_token.check_token(user, token):
            user.is_active = True
            user.save()

            # Start a transaction to ensure atomicity
            with transaction.atomic():
                # Get or create the profile
                tel_id = message.from_user.id
                tel_username = message.from_user.username
                tel_first_name = message.from_user.first_name
                tel_last_name = message.from_user.last_name

                profile, created = ProfileModel.objects.get_or_create(
                    tel_id=tel_id,
                    defaults={
                        "telegram": tel_username,
                        "fname": tel_first_name,
                        "lname": tel_last_name,
                        "user": user,
                        "user_level": ProfileModel.UserLevel.GREEN,
                    }
                )

                if not created:
                    # Update existing profile with the user and level if it already exists
                    profile.user = user
                    profile.user_level = ProfileModel.UserLevel.GREEN
                    profile.save()

            app.send_message(message.chat.id, f"{message.from_user.first_name} عزیز حساب شما فعال شد.")
            main_menu = ProfileModel.objects.get(tel_id=message.from_user.id).tel_menu
            extra_buttons = ProfileModel.objects.get(tel_id=message.from_user.id).extra_button_menu
            markup = send_menu(message, main_menu, "main_menu", extra_buttons)
            app.send_message(message.chat.id, "لطفا یکی از گزینه های زیر را انتخاب کنید:", reply_markup=markup)
        else:
            app.send_message(message.chat.id, "لینک فعالسازی نامعتبر است یا منقضی شده است.")
    except IntegrityError as e:
        # Catch IntegrityError for unique constraint failure on `telegram`
        if 'UNIQUE constraint failed' in str(e):
            app.send_message(message.chat.id,
                             "این شماره تلگرام قبلا ثبت شده است. لطفا از شماره تلگرام دیگری استفاده کنید.")
        else:
            app.send_message(message.chat.id, f"خطا: {e}")
            raise e
    except Exception as e:
        app.send_message(message.chat.id, f"خطا: {e}")  # Log error


@app.message_handler(func=lambda message: message.text.startswith("/start store_"))
def handle_store_product_start(message):
    try:
        parts = message.text.split("_")
        if len(parts) != 4:  # باید بشه: /start store {store_id} product {product_id}
            app.send_message(message.chat.id, "لینک خرید معتبر نیست.")
            return

        _, store_id, _, product_id = parts  # /start store_5_product_12

        

        # ست کردن فروشگاه جاری
        profile = ProfileModel.objects.get(tel_id=message.from_user.id)
        profile.server_store = Store.objects.get(id=store_id)
        profile.seller_mode = False
        profile.save()

        start(message)

        product = Product.objects.get(code=product_id)
        attributes = product.attributes.all()
        product_handler = ProductHandler(app, Product.objects.get(code=product_id), current_site, attributes=attributes)
        product_handler.send_product_message(message.chat.id)

    
    except Exception as e:
        print(traceback.format_exc())
        app.send_message(message.chat.id, f"⚠ خطا در پردازش لینک خرید: {e}")


# Start handler
@app.message_handler(commands=['start'])
def start(message):
    try:
        tel_id = message.from_user.id
        tel_username = message.from_user.username
        tel_first_name = message.from_user.first_name
        tel_last_name = message.from_user.last_name
        
        response = requests.post(f"{current_site}/telbot/api/check-registration/", json={"tel_id": tel_id})
        print(response.status_code)

        profile, created = ProfileModel.objects.get_or_create(tel_id=tel_id, telegram=tel_username,
                                                              fname=tel_first_name, lname=tel_last_name)

        

        if created:
            language_setting(message)
        else:
            home(message)

    except Exception as e:
        error_details = traceback.format_exc()
        custom_message = f"An error occurred in start handler: {e}\nDetails:\n{error_details}"
        app.send_message(message.chat.id, t(message, "start_error"))
        print(custom_message)



#####################################################################################################

# HOME
@app.message_handler(func=lambda message: message.text == "🏡")
def home(message, text=None):
    try:
        if isinstance(message, types.Message):
            message = message
            call_data = None
            is_callback = False
            id = message.from_user.id
        else:
            message = message.message
            is_callback = True
            id = message.chat.id
    except Exception as e:
        error_details = traceback.format_exc()
        custom_message = f"An error occurred: {e}\nDetails:\n{error_details}"
        print(f"{custom_message}")

    if subscription.subscription_offer(message):
        session_manager.reset_user_session(message.chat.id, namespace="address")
        session_manager.reset_user_session(message.chat.id, namespace="menu")
        session_manager.reset_user_session(message.chat.id, namespace="add_product")
        session_manager.reset_user_session(message.chat.id, namespace="delete_product")

        profile = ProfileModel.objects.get(tel_id=id)
        markup = send_menu(message, profile.tel_menu, "main_menu", profile.extra_button_menu)
        if not text:
            text = t(message, "home_message")
        app.send_message(message.chat.id, text, reply_markup=markup)


# Visit website
@app.message_handler(func=lambda message: message.text == t(message, "visit_website"))
def visit_website(message):
    if subscription.subscription_offer(message):
        send_website_link(message)


# settings handler
@app.message_handler(func=lambda message: message.text == t(message, "menu_settings"))
def settings(message):
    if subscription.subscription_offer(message):
        home_menue = ["🏡"]
        markup = send_menu(message, ProfileModel.objects.get(tel_id=message.from_user.id).settings_menu, "settings",
                           home_menue, 2)
        app.send_message(message.chat.id, t(message, "settings_message"), reply_markup=markup)


# profile settings handler
@app.message_handler(func=lambda message: message.text in (translations["menu_profile"][ProfileModel.objects.get(tel_id=message.chat.id).lang]))
def profile_setting(message):
    if subscription.subscription_offer(message):
        home_menue = ["🏡"]
        markup = send_menu(message, ProfileModel.objects.get(tel_id=message.from_user.id).profile_menu, "profile",
                           home_menue)
        app.send_message(message.chat.id, t(message, "profile_settings"), reply_markup=markup)

# balance
@app.message_handler(func=lambda message: message.text == translations["menu_balance"][ProfileModel.objects.get(tel_id=message.chat.id).lang])
def balance_menue(message):
    if subscription.subscription_offer(message):
        options = [t(message, "my_balance"), t(message, "increase_balance")]
        home_menue = ["🏡"]
        markup = send_menu(message, options, "balance_category", home_menue)
        app.send_message(message.chat.id, t(message, "balance_menue"), reply_markup=markup)

# language settings handler
@app.message_handler(func=lambda message: message.text in (translations["menu_language"][ProfileModel.objects.get(tel_id=message.chat.id).lang]))
def language_setting(message):
    try:
        if subscription.subscription_offer(message):
            def get_language_choices():
                language_map = {
                    'fa': '🇮🇷 فارسی',
                    'en': '🇬🇧  English',
                    'zh': '🇨🇳  中国人',
                    'ru': '🇷🇺  русский',
                    'ar': '🇵🇸  عربیة',
                }
                return [name for code, name in language_map.items()]

            markup = send_menu(message, get_language_choices(), "language_menu", retun_menue)

            app.send_message(
                message.chat.id,
                t(message, "language_setting"),
                reply_markup=markup
            )

    except Exception as e:
        error_details = traceback.format_exc()
        print(f"{error_details}")

# become a seller handler
@app.message_handler(func=lambda message: message.text in (translations["menu_become_seller"][ProfileModel.objects.get(tel_id=message.chat.id).lang]))
def become_a_seller(message):
    if subscription.subscription_offer(message):
        try:
            profile = ProfileModel.objects.get(tel_id=message.from_user.id)
            Store.objects.get(owner=ProfileModel.objects.get(tel_id=message.from_user.id))
            profile.seller_mode = True
            profile.settings_menu = profile.LEVEL_MENUS["seller"][2]
            profile.save()
            profile.save()
            markup = send_menu(message, profile.tel_menu, "settings", profile.extra_button_menu)
            app.send_message(message.chat.id, t(message, "become_a_seller"), reply_markup=markup)
        except Store.DoesNotExist:
            app.send_message(message.chat.id, t(message, "become_a_seller_no_store"))


# back to buyer mode handler# become a seller handler
@app.message_handler(func=lambda message: message.text in (translations["menu_back_to_buyer"][ProfileModel.objects.get(tel_id=message.chat.id).lang]))
def back_to_buyer(message):
    if subscription.subscription_offer(message):
        profile = ProfileModel.objects.get(tel_id=message.from_user.id)
        profile.seller_mode = False
        profile.settings_menu = profile.LEVEL_MENUS[profile.user_level][2]
        profile.save()
        profile.save()

        home(message)


import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
import arabic_reshaper
from bidi.algorithm import get_display
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from django.core.cache import cache
import tempfile
import gc

def generate_sales_pdf(store, sales_data, message_text, font_path):
    """تابع جداگانه برای تولید PDF در thread جداگانه"""
    try:
        # ایجاد فایل موقت در حافظه
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            file_path = temp_file.name

        # تنظیمات PDF
        p = canvas.Canvas(file_path, pagesize=A4)
        p.setFont("Vazir", 12)  # کاهش سایز فونت برای صرفه‌جویی در فضا
        
        border_margin = 20  # کاهش حاشیه
        
        def draw_header_footer(page_num):
            p.setStrokeColorRGB(0, 0, 0)
            p.setLineWidth(2)  # کاهش ضخامت خط
            p.rect(border_margin, border_margin, A4[0] - 2 * border_margin, A4[1] - 2 * border_margin)
            
            # حذف لوگو برای کاهش حجم فایل
            title_text = get_display(arabic_reshaper.reshape(
                message_text("sale_statistics_title", store_name=store.name)
            ))
            p.drawCentredString(A4[0] / 2, A4[1] - 80, title_text)
            
            # شماره صفحه کوچک‌تر
            p.setFont("Vazir", 8)
            p.drawCentredString(A4[0] / 2, border_margin - 12, f"Page {page_num}")
            p.setFont("Vazir", 12)

        # هدرهای جدول با ستون‌های بهینه‌شده
        headers = [
            get_display(arabic_reshaper.reshape(message_text("sale_statistics_index"))),
            get_display(arabic_reshaper.reshape(message_text("sale_statistics_date"))),
            get_display(arabic_reshaper.reshape(message_text("sale_statistics_quantity"))),
            get_display(arabic_reshaper.reshape(message_text("sale_statistics_total_cost"))),
            get_display(arabic_reshaper.reshape(message_text("sale_statistics_product_name"))),
        ]
        
        data = [headers]
        total_amount = 0
        max_rows_per_page = 25  # افزایش تعداد ردیف در هر صفحه
        start_y = A4[1] - 120  # تنظیم موقعیت شروع
        page_num = 1
        
        draw_header_footer(page_num)
        
        # پردازش داده‌های فروش
        for idx, sale in enumerate(sales_data, start=1):
            total_amount += sale['total_price']
            row = [
                str(idx),
                get_display(arabic_reshaper.reshape(sale['date'])),
                str(sale['quantity']),
                f"{sale['total_price']:,.0f}",
                get_display(arabic_reshaper.reshape(sale['product_name'][:30])),  # محدود کردن طول نام محصول
            ]
            data.append(row)
            
            # ایجاد صفحه جدید در صورت نیاز
            if len(data) > max_rows_per_page:
                table = Table(data, colWidths=[40, 70, 50, 80, 120])  # عرض ستون‌های بهینه‌شده
                table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), 'Vazir'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),  # فونت کوچک‌تر
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),  # خطوط نازک‌تر
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ]))
                
                table_x = border_margin + 10
                table_y = start_y - (max_rows_per_page * 18) - 20  # کاهش فاصله
                table.wrapOn(p, A4[0], A4[1])
                table.drawOn(p, table_x, table_y)
                
                p.showPage()
                p.setFont("Vazir", 12)
                page_num += 1
                draw_header_footer(page_num)
                data = [headers]
        
        # ردیف مجموع
        total_row = [
            "", 
            "", 
            "", 
            f"{total_amount:,.0f}", 
            get_display(arabic_reshaper.reshape(message_text("sale_statistics_total")))
        ]
        data.append(total_row)
        
        # جدول نهایی
        table = Table(data, colWidths=[40, 70, 50, 80, 120])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Vazir'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('SPAN', (3, -1), (4, -1)),
        ]))
        
        table_x = border_margin + 10
        table_y = start_y - (len(data) * 18) - 20
        table.wrapOn(p, A4[0], A4[1])
        table.drawOn(p, table_x, table_y)
        
        p.save()
        return file_path
        
    except Exception as e:
        # پاک‌سازی در صورت خطا
        if 'file_path' in locals() and os.path.exists(file_path):
            os.unlink(file_path)
        raise e

@app.message_handler(func=lambda message: message.text == t(message, "menu_sale_statistics"))
def sale_statistics(message):
    try:
        # بررسی سریع subscription
        if not subscription.subscription_offer(message):
            return

        chat_id = message.chat.id
        cache_key = f"sale_stats_{chat_id}_{datetime.now().strftime('%Y%m%d')}"
        
        # بررسی کش برای جلوگیری از پردازش تکراری
        if cache.get(cache_key):
            app.send_message(chat_id, "در حال پردازش درخواست قبلی... لطفاً چند لحظه صبر کنید.")
            return
        
        cache.set(cache_key, True, 300)  # کش به مدت 5 دقیقه

        profile = ProfileModel.objects.get(tel_id=message.from_user.id)
        store = Store.objects.filter(owner=profile).first()

        if not store:
            app.send_message(chat_id, t(message, "sale_statistics_no_store"))
            cache.delete(cache_key)
            return

        if not profile.seller_mode:
            app.send_message(chat_id, t(message, "not_a_seller_sale_statistics"))
            cache.delete(cache_key)
            return

        # دریافت داده‌های فروش با کوئری بهینه
        sales = Sale.objects.filter(
            seller=store
        ).select_related('product').only(
            'created_at', 'quantity', 'total_price', 'product__name'
        ).order_by("-created_at")[:1000]  # محدود کردن به 1000 رکورد اخیر

        if not sales.exists():
            app.send_message(chat_id, t(message, "sale_statistics_no_sale"), parse_mode="HTML")
            cache.delete(cache_key)
            return

        # آماده‌سازی داده‌ها برای پردازش
        sales_data = []
        for sale in sales:
            sales_data.append({
                'date': sale.created_at.strftime('%Y-%m-%d'),
                'quantity': sale.quantity,
                'total_price': sale.total_price,
                'product_name': sale.product.name
            })

        # ارسال پیام "در حال پردازش"
        processing_msg = app.send_message(chat_id, "📊 در حال تولید گزارش...")

        def generate_and_send_pdf():
            try:
                font_path = os.path.join(sett.MEDIA_ROOT, "fonts", "Vazir.ttf")
                if not os.path.exists(font_path):
                    raise FileNotFoundError("فونت Vazir یافت نشد")

                pdfmetrics.registerFont(TTFont("Vazir", font_path))
                
                # تولید PDF در thread جداگانه
                file_path = generate_sales_pdf(store, sales_data, t, font_path)
                
                # ارسال فایل
                with open(file_path, "rb") as pdf_file:
                    app.send_document(chat_id, pdf_file, 
                                    caption=t(message, "sale_statistics_ready"))
                
                # حذف فایل موقت
                os.unlink(file_path)
                
                # پاک‌سازی حافظه
                gc.collect()
                
            except Exception as e:
                app.send_message(chat_id, t(message, "sale_statistics_error"))
                print(f"Error generating PDF: {traceback.format_exc()}")
            finally:
                # حذف پیام در حال پردازش و پاک‌سازی کش
                try:
                    app.delete_message(chat_id, processing_msg.message_id)
                except:
                    pass
                cache.delete(cache_key)

        # اجرای تولید PDF در thread جداگانه
        import threading
        thread = threading.Thread(target=generate_and_send_pdf)
        thread.daemon = True
        thread.start()

        # پاسخ فوری به کاربر
        app.send_message(chat_id, "✅ درخواست شما دریافت شد. گزارش در حال آماده‌سازی است...")

    except Exception as e:
        error_message = traceback.format_exc()
        print(f"Sale statistics error: {error_message}")
        app.send_message(message.chat.id, t(message, "sale_statistics_error"))
        
        # پاک‌سازی کش در صورت خطا
        cache_key = f"sale_stats_{message.chat.id}_{datetime.now().strftime('%Y%m%d')}"
        cache.delete(cache_key)


        
@app.callback_query_handler(
    func=lambda call: "increase_" in call.data or "decrease_" in call.data or "addtocart_" in call.data)
def handle_product_buttons(call):
    try:
        data = call.data.split("_")
        action = data[0]  # increase, decrease, addtocart
        
        # استخراج product_code (همیشه در index 1 هست)
        if len(data) < 2:
            app.answer_callback_query(call.id, "داده‌های نامعتبر!", show_alert=True)
            return
            
        product_code = str(data[1])

        if not product_code:
            app.answer_callback_query(call.id, "کد محصول نامعتبر است!", show_alert=True)
            return

        try:
            product = Product.objects.get(code=product_code)
        except Product.DoesNotExist:
            app.answer_callback_query(call.id, "محصول یافت نشد!", show_alert=True)
            return

        product_handler = ProductHandler(app, product, current_site, attributes=product.attributes.all())
        
        # هندلرها خودشون variant_id رو از call.data استخراج می‌کنن
        if action == "addtocart":
            product_handler.handle_add_to_cart(call)
        else:
            product_handler.handle_buttons(call)

    except Exception as e:
        error_message = traceback.format_exc()
        print(f"Error in handle_product_buttons: {e}\n{error_message}")
        app.answer_callback_query(call.id, "خطا در پردازش درخواست!", show_alert=True)

@app.callback_query_handler(func=lambda call: "VarPrev_" in call.data or "VarNext_" in call.data)
def handle_variant_navigation(call):
    try:
        data = call.data.split("_")
        product_code = str(data[1]) if len(data) > 1 else None
        
        if not product_code:
            return

        product = Product.objects.get(code=product_code)
        product_handler = ProductHandler(app, product, current_site, attributes=product.attributes.all())
        product_handler.handle_variant_navigation(call)

    except ObjectDoesNotExist:
        app.answer_callback_query(call.id, "محصول یافت نشد!", show_alert=True)
    except Exception as e:
        error_message = traceback.format_exc()
        print(f"Error in handle_variant_navigation: {e}\n{error_message}")
        app.answer_callback_query(call.id, "خطا در تغییر واریانت!", show_alert=True)


@app.callback_query_handler(func=lambda call: "comments_" in call.data)
def handle_comments(call):
    try:
        data = call.data.split("_")
        product_code = str(data[1]) if len(data) > 1 else None
        
        if not product_code:
            return

        product = Product.objects.get(code=product_code)
        product_handler = ProductHandler(app, product, current_site, attributes=product.attributes.all())
        product_handler.handle_comments(call)

    except ObjectDoesNotExist:
        app.answer_callback_query(call.id, "محصول یافت نشد!", show_alert=True)
    except Exception as e:
        error_message = traceback.format_exc()
        print(f"Error in handle_comments: {e}\n{error_message}")


@app.callback_query_handler(func=lambda call: any(x in call.data for x in ["remove", "add", "reduce"]))
def handle_cart_operations(call):
    try:
        data = call.data.split("_")
        action = data[0]  # remove, sudoincrease
        
        if action == "remove":
            send_cart = SendCart(app, call.message)
            send_cart.remove_item(call)
            return
            
        if action == "add" or action == "reduce":
            send_cart = SendCart(app, call.message)
            send_cart.add(call)
            return

    except Exception as e:
        error_message = traceback.format_exc()
        print(f"Error in handle_cart_operations: {e}\n{error_message}")


@app.message_handler(func=lambda message: message.text == t(message, "menu_cart"))
@app.callback_query_handler(func=lambda call: call.data.startswith("product_show_") or call.data == "pay")
@app.callback_query_handler(func=lambda call: call.data == "finalize" or call.data == "view_cart")
def cart_CallBack(data):
    try:
        if isinstance(data, types.Message):
            cart = SendCart(app, data)
            if cart.cart:
                cart.send(data)
        elif isinstance(data, types.CallbackQuery):
            cart = SendCart(app, data.message)
            if cart.cart:
                if data.data == "finalize" or data.data == "view_cart":
                    cart.send(data)
                else:
                    cart.handle_buttons(data)
    except Exception as e:
        print(f"Error in phone_handler: {e}\n{traceback.format_exc()}")

@app.callback_query_handler(func=lambda call: call.data == "confirm order")
def confirm_order_CallBack(data):
    cart = SendCart(app, data.message)
    if cart.cart:  # بررسی اینکه سبد خرید موجود باشد
        cart.invoice(data)


@app.callback_query_handler(func=lambda call: call.data == "payment")
def payment_order_CallBack(data):
    cart = SendCart(app, data.message)
    if cart.cart:
        cart.invoice(data)



# 10 products
@app.message_handler(
    func=lambda message: message.text in (t(message, "most_selling"), t(message, "most_expensive"), t(message, "most_discounted"), t(message, "cheapest")))
def handle_ten_products(message):
    if subscription.subscription_offer(message):
        session = session_manager.get_user_session(message.chat.id, namespace="menu")
        current_menu = session["current_menu"]

        if message.text == t(message, "most_discounted"):
            products = Product.objects.annotate(lower_title=Lower('category__title')).filter(
                lower_title=current_menu.lower(), discount__gt=0, status=True, category__status=True
            ).order_by("discount")[:10]
        elif message.text == t(message, "most_selling"):
            app.send_message(message.chat.id, t(message, "most_selling_feature_not_available"))
            return
        elif message.text == t(message, "cheapest"):
            products = Product.objects.annotate(lower_title=Lower('category__title')).filter(
                lower_title=current_menu.lower(), status=True, category__status=True
            ).order_by("-price")[:10]
        elif message.text == t(message, "most_expensive"):
            products = Product.objects.annotate(lower_title=Lower('category__title')).filter(
                lower_title=current_menu.lower(), status=True, category__status=True
            ).order_by("price")[:10]


        if not products.exists():
            app.send_message(message.chat.id, t(message, "no_products_in_category"))
            return

        for product in products:
            try:
                product_handler = ProductHandler(app, product, current_site, attributes=product.attributes.all())
                product_handler.send_product_message(message.chat.id)
            except Exception as e:
                app.send_message(message.chat.id, f"the error is: {e}")





@app.message_handler(func=lambda message: (
        session_manager.get_user_session(message.chat.id, namespace="phone") != {} and
        session_manager.get_user_session(message.chat.id, namespace="phone")["state"] in ("take_phone",)))
@app.callback_query_handler(func=lambda call: call.data == "phone")
def phone_handler(data):
    try:

        if isinstance(data, types.Message):
            message = data
            call_data = None
            is_callback = False
        else:
            message = data.message
            call_data = data.data
            is_callback = True
            app.answer_callback_query(data.id)
        phone = SendPhone(app, message)

        if not is_callback:

            if session_manager.get_user_session(message.chat.id, namespace="phone")["state"] == "take_phone":
                phone.really_take_phone(message)
        else:
            phone.take_phone(data)

    except Exception as e:
        print(f"Error in phone_handler: {e}\n{traceback.format_exc()}")
        # chat_id = data.message.chat.id if hasattr(data, 'message') else data.chat.id
        # app.send_message(chat_id,
        #                  f"خطایی در گرفتن شماره تماس رخ داد. لطفاً مجدداً تلاش کنید. : {e}\n{traceback.format_exc()}")



@app.message_handler(func=lambda message: 
    message.text == t(message, "menu_my_address") 
    or (
        session_manager.get_user_session(message.chat.id, namespace="address") != {} 
        and session_manager.get_user_session(
            message.chat.id, 
            namespace="address"
        ).get("state") in ("address_selection_zipcode", "address_selection_street")
    )
)
@app.callback_query_handler(func=lambda call: call.data.startswith(
    ("address", "show_address", "close_addresses", 'delete_address_', 'add_new_address', 'manual_add_address', 'next',
     'prev', 'country_', 'province_', 'city_', '_back', "change_address")) or call.data in ("back_to_addresses"))
def unified_address_handler(data):
    try:

        if isinstance(data, types.Message):
            message = data
            call_data = None
            is_callback = False
        else:
            message = data.message
            call_data = data.data
            is_callback = True
        loc = SendLocation(app, message)
        session = session_manager.get_user_session(message.chat.id, namespace="address")
        
        if call_data == "_back":
            state = [
                "show_addresses",
                "show_single_address",
                "add_new_address",
                "manual_add_address",
                "address_selection_country",
                "address_selection_province",
                "address_selection_city",
            ]

            old_state = session["state"]
            session["state"] = state[state.index(old_state) - 1]
            session_manager.set_user_session(message.chat.id, session, namespace="address")

        if not is_callback:

            if message.text == t(message, "menu_my_address") :
                session['from my postal address'] = True
                session_manager.set_user_session(message.chat.id, session, namespace="address")
                loc.show_addresses()
            elif session.get("state") == "address_selection_street":
                loc.handle_picked_street(message)
            elif session.get("state") == "address_selection_zipcode":
                loc.handle_picked_zipcode(message)

        elif call_data == "address_close":
            session_manager.reset_user_session(data.message.chat.id, namespace="address")
            app.delete_message(data.message.chat.id, data.message.message_id)
            data.message.text = "🏡"
            home(data)
        
        elif call_data in ("address", "back_to_addresses"):
            loc.show_addresses(data)
        elif call_data.startswith("show_address_"):
            address_id = int(call_data.split("_")[-1])
            address = Address.objects.get(id=address_id)
            loc.show_single_address(address, data)
        elif call_data.startswith("address_"):
            pass# loc.show_single_address(data, address)
        
        elif call_data.startswith('close_address'):
            loc.handle_close(data)
        elif call_data.startswith('delete_address_'):
            address_id = int(call_data.split("_")[-1])
            address = Address.objects.get(id=address_id)
            loc.delete_address(data, address)
        elif call_data.startswith("add_new_address"):
            loc.add_new_address(data)
        elif call_data.startswith("manual_add_address") or call_data.startswith("change_address"):
            if call_data.startswith("change_address"):
                address_id = int(call_data.split("_")[-1])
                session['change_address'] = (True, address_id)
                session_manager.set_user_session(message.chat.id, session, namespace="address")
            loc.manual_add_address(data)
        elif call_data.startswith("next"):
            loc.handle_next(data)
        elif call_data.startswith("prev"):
            loc.handle_prev(data)
        elif call_data.startswith("country_"):
            loc.handle_picked_country(data)
        elif call_data.startswith("province_"):
            loc.handle_picked_province(data)
        elif call_data.startswith("city_"):
            loc.handle_picked_city(data)
        elif (session != {} and session["state"] == 'show_addresses'):
            loc.show_addresses(data)
        elif (session != {} and session["state"] == 'manual_add_address'):
            print("manual_add_address")
            loc.add_new_address(data)
        elif (session != {} and session["state"] == 'address_selection_country'):
            print("address_selection_country")
            loc.manual_add_address(data)
        elif (session != {} and session["state"] == 'address_selection_province'):
            print("address_selection_province")
            loc.handle_picked_country(data)
        elif (session != {} and session["state"] == 'address_selection_city'):
            print("address_selection_city")
            loc.handle_picked_province(data)
        else:
            app.send_message(message.chat.id, t(message, "invalid_command"))
    except Address.DoesNotExist:
        app.send_message(message.chat.id, t(message, "address_not_found"))
    except Exception as e:
        print(f"Error in unified_address_handler: {e}\n{traceback.format_exc()}")


@app.message_handler(func=lambda message: (session_manager.get_user_session(message.chat.id, namespace="address") != {}) and (session_manager.get_user_session(message.chat.id, namespace="address")["change_postal"][0]))
def change_postal_enter_new(message):
    loc = SendLocation(app, message)
    session = session_manager.get_user_session(message.chat.id, namespace="address")
    loc.handle_picked_zipcode(message)
    session['change_postal'] = None
    session_manager.set_user_session(message.chat.id, session, namespace="address") 


@app.callback_query_handler(func=lambda call: call.data.startswith(("select_address",)))
def select_address(call):
    try:
        loc = SendLocation(app, call.message)
        address_id = int(call.data.split("_")[-1])
        address = Address.objects.get(id=address_id)
        loc.select_address(call, address)
    except Exception as e:
        print(e)


@app.callback_query_handler(func=lambda call: call.data.startswith(("change_postal",)))
def change_postal(call):
    try:
        app.answer_callback_query(call.id, text=t(call.message, "change_postal_code"), show_alert=False)
        address_id = int(call.data.split("_")[-1])
        session = session_manager.get_user_session(call.message.chat.id, namespace="address")
        session["change_postal"] = tuple((True, address_id))
        session_manager.set_user_session(call.message.chat.id, session, namespace="address")
        
        text = t(call.message, "enter_postal_code")

        markup = SendMarkup(
                bot=app,
                chat_id=call.message.chat.id,
                text=text,
                buttons=None,
                button_layout=None,
                handlers=None
            )


        markup.edit(call.message.message_id) 
    except Exception as e:
        print(f"Error in change_postal handler: {e}\n{traceback.format_exc()}")




@app.message_handler(func=lambda message: message.text in ('🇮🇷 فارسی', '🇬🇧  English', '🇨🇳  中国人', '🇷🇺  русский', '🇵🇸  عربیة',))
def change_lang(message):
    try:
        profile = ProfileModel.objects.get(tel_id=message.chat.id)
        if 'فارسی' in message.text:
            profile.lang = 'fa'
        elif 'English' in message.text:
            profile.lang = 'en'
        elif "中国人" in message.text:
            profile.lang = 'zh'
        elif "русский" in message.text:
            profile.lang = 'ru'
        elif "عربیة" in message.text:
            profile.lang = 'ar'
        profile.save()
        app.delete_message(message.chat.id, message.message_id)
        home(message, text=t(message, "your_lang_changed"))
        
    except Exception as e:
        print(f"Error in change language handler: {e}\n{traceback.format_exc()}")


# Back to Previous Menu
@app.message_handler(func=lambda message: message.text == "🔙")
def handle_back(message):
    if subscription.subscription_offer(message):
        try:
            session = session_manager.get_user_session(message.chat.id, namespace="menu")
            try:
                previous_category_title = Category.objects.get(
                    title__iexact=session["current_menu"], status=True
                ).get_parents()[0].title

                fake_message = message
                fake_message.text = previous_category_title
                subcategory(fake_message)
            except IndexError as e:
                if "list index out of range" in str(e):
                    fake_message = message
                    fake_message.text = t(message, "menu_categories")
                    category_client(fake_message)
        except Exception as e:
            app.send_message(message.chat.id, f"the error is: {e}")



# fill address and phone nukber field for the payment link to be activated
@app.callback_query_handler(func=lambda call: call.data == "phone_address_required")
def address_phone_required(data):
   app.answer_callback_query(data.id, t(data.message, "address_and_phone_required"), show_alert=True) 



# show balance
@app.message_handler(func=lambda message: message.text == t(message, "my_balance"))
def my_balance(message):
    if subscription.subscription_offer(message):
        show_balance(message)


# Buy products with code
@app.message_handler(func=lambda message: message.text == t(message, "menu_buy_by_code"))
def buy_with_code(message):
    if subscription.subscription_offer(message):
        ask_for_product_code(message)


##################################


@app.message_handler(state=Support.code)
def handle_product_code(message):
    if subscription.subscription_offer(message):
        try:
            chat_id = message.chat.id
            product_code = message.text
            if re.match(r'^\d{10}$', message.text):

                if Product.objects.filter(code=message.text, status=True, category__status=True).exists():
                    product = Product.objects.get(code=message.text, status=True, category__status=True)
                    try:
                        product_handler = ProductHandler(app, product, current_site, attributes=product.attributes.all())
                        product_handler.send_product_message(message.chat.id)
                    except Exception as e:
                        app.send_message(message.chat.id, f"the error is: {e}")
                elif Product.objects.filter(code=message.text, status=False, category__status=True).exists():
                    app.send_message(message.chat.id, t(message, "product_disabled_by_seller"))
                elif Product.objects.filter(code=message.text, status=True, category__status=False).exists():
                    app.send_message(message.chat.id,
                                    f"دسته بندی {Product.objects.get(code=message.text, status=True, category__status=False).category.title} توسط فروشنده غیرفعال شده است لذا همه کالاهای موجود در این دسته بندی از جمله کالای مورد نظر شما نیز غیر فعال هستند.\n\n برای کسب اطلاع بیشتر با پشتیبان این فروشگاه ارتباط بگیرید.")
                else:
                    # No product found with this code
                    app.send_message(message.chat.id, t(message, "product_not_found"))

            else:
                app.send_message(chat_id, t(message, "invalid_code"))
            app.delete_state(user_id=message.from_user.id, chat_id=message.chat.id)
        except Exception as e:
            print(f"the error is: {e}")


#####################################################################################
# support handlers


# Handling the 'Support 👨🏻‍💻' button click event
@app.message_handler(func=lambda message: message.text == t(message, "menu_support"))
def sup(message):
    app.send_message(chat_id=message.chat.id,
                     text=t(message, "start_support_chat"))
    app.set_state(user_id=message.from_user.id, state=Support.text, chat_id=message.chat.id)


# Handling the user's first message which is saved in 'Support.text' state
@app.message_handler(state=Support.text)
def sup_text(message):
    try:
        sup_markup = types.InlineKeyboardMarkup()
        client_markup = types.InlineKeyboardMarkup()

        sup_markup.add(types.InlineKeyboardButton(text=t(message, "reply"), callback_data="پاسخ"))
        client_markup.add(types.InlineKeyboardButton(text=t(message, "end_chat"), callback_data="پایان مکالمه"))

        app.send_message(chat_id=5629898030,
                         text=t(message, "user_message_received", user_id=message.from_user.id, username=message.from_user.username, text=escape_special_characters(message.text))
,
                         reply_markup=sup_markup, parse_mode="HTML")

        app.send_message(chat_id=message.chat.id, text=t(message, "message_sent"),
                         reply_markup=client_markup)

        texts[message.from_user.id] = message.text


    except Exception as e:
        error_message = traceback.format_exc()
        print(f"your error is: {error_message}")


# هندلر برای دکمه "ثبت نام می‌کنم"
@app.message_handler(func=lambda message: message.text == "🔐     ایجاد حساب کاربری    🛡️")
def ask_username(message):
    if subscription.subscription_offer(message):
        try:
            app.send_message(message.chat.id, "ممکنه لطفا ایمیلت رو وارد کنی:")
            app.register_next_step_handler(message, pick_email)
        except Exception as e:
            error_message = traceback.format_exc()
            print(f"your error is: {error_message}")

##################################### PRODUCT #####################################

@app.message_handler(func=lambda message: message.text == t(message, "product"))
def product(message):
    if subscription.subscription_offer(message):
        profile = ProfileModel.objects.get(tel_id=message.from_user.id)
        if profile.seller_mode:
            home_menue = ["🏡"]
            session_manager.reset_user_session(message.chat.id, namespace="add_product")
            session_manager.reset_user_session(message.chat.id, namespace="delete_product")
            session_manager.reset_user_session(message.chat.id, namespace="deactivate_product")
            session = session_manager.get_user_session(message.chat.id, namespace="menu")
            session['product'] = True
            session['category'] = False
            session_manager.set_user_session(message.chat.id, session, namespace="menu")
            markup = send_menu(message, [t(message, "menu_add"), t(message, "menu_delete"), t(message, "menu_deactivate"), t(message, "edit"), t(message, "my_products_list")], "product", home_menue)
            app.send_message(message.chat.id, t(message, "what_action_on_product"), reply_markup=markup)
        else:
            app.send_message(message.chat.id, t(message, "not_a_seller_edit_products"))



@app.message_handler(func=lambda m: m.text == t(m, "menu_add"))
def add_handler(message):
    session = session_manager.get_user_session(message.chat.id, namespace="menu")
    session["menu_add"] = True
    session_manager.set_user_session(message.chat.id, session, namespace="menu")

    if session.get("category"):
        # Category deletion
        category_class = CategoryClass()
        category_class.handle_category(message)

    elif session.get("product"):
        # Product deletion
        add_product(message)



#####################################    ADD PRODUCT    #####################################


def add_product(message):
    """Start the product addition process."""
    try:
        if subscription.subscription_offer(message):
            profile = ProfileModel.objects.get(tel_id=message.from_user.id)
            if profile.seller_mode:
                try:
                    if not get_user_store(message).categories.exists():
                        # فروشگاه هیچ دسته‌بندی ندارد
                        app.send_message(message.chat.id, t(message, "no_categories_to_add_product"))
                        return
#                    product_bot.get_name(message)
                    markup = send_menu(message, [t(message, "cancel_action")], message.text)
                    app.send_message(message.chat.id, t(message, "enter_product_name"), reply_markup=markup)
                    session = session_manager.get_user_session(message.chat.id, namespace="menu")
                    session['add_product'] = True
                    session_manager.set_user_session(message.chat.id, session, namespace="menu")
		    
                    session_manager.set_user_session(message.chat.id, {"brand": True}, namespace="add_product")
                except Exception as e:
                    print(e)
            else:
                app.send_message(message.chat.id, t(message, "not_a_seller_add_product"))
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"{error_details}")

@app.message_handler(func=lambda message: message.text == t(message, "cancel_action"))
def cancel_action(message):
    try:
        session = session_manager.get_user_session(message.chat.id, namespace="menu")
        if session.get("add_product") or session.get("delete_product") or session.get("deavtivate_product") or session.get("product_list"):
            print("yes")
            product_bot.cancle_request(message)
            product(message)
        elif session.get("category"):
            category(message)
    except Exception:
        print(traceback.format_exc())


@app.message_handler(func=lambda message: session_manager.get_user_session(message.chat.id, namespace="add_product").get("brand"))
def add_product_get_brand(message):
    try:
        product_bot.get_name(message)
    except Exception:
        print(traceback.format_exc())

@app.message_handler(func=lambda message: session_manager.get_user_session(message.chat.id, namespace="add_product").get("price"))
def add_product_get_price(message):
    try:
        product_bot.get_brand(message)
    except Exception:
        print(traceback.format_exc())

@app.message_handler(func=lambda message: session_manager.get_user_session(message.chat.id, namespace="add_product").get("discount"))
def add_product_get_discount(message):
    try:
        product_bot.get_price(message)
    except Exception:
        print(traceback.format_exc())

@app.message_handler(func=lambda message: session_manager.get_user_session(message.chat.id, namespace="add_product").get("status"))
def add_product_get_status(message):
    try:
        product_bot.get_discount(message)
    except Exception:
        print(traceback.format_exc())

@app.message_handler(func=lambda message: session_manager.get_user_session(message.chat.id, namespace="add_product").get("category"))
def add_product_get_category(message):
    try:
        product_bot.get_status(message)
    except Exception:
        print(traceback.format_exc())

@app.message_handler(func=lambda message: message.text in [t(message, "accurate_inventory"), t(message, "not_necessary")] and session_manager.get_user_session(message.chat.id, namespace="add_product").get("ask_variant_decision"))
def add_product_ask_variant_decision(message):
    try:
        if message.text == t(message, "accurate_inventory"):
            product_bot.get_variant_decision(message)
        elif message.text == t(message, "not_necessary"):
            product_bot.get_stock(message)
    except Exception:
        print(traceback.format_exc())

@app.message_handler(func=lambda message: session_manager.get_user_session(message.chat.id, namespace="add_product").get("variantkey"))
def get_variant_key(message):
    try:
        product_bot.get_variant_key(message)
    except:
        print(traceback.format_exc())


@app.message_handler(func=lambda message: session_manager.get_user_session(message.chat.id, namespace="add_product").get("variantvalue"))
def get_variant_values(message):
    try:
        product_bot.get_variant_values(message)
    except:
        print(traceback.format_exc())


@app.message_handler(func=lambda message: session_manager.get_user_session(message.chat.id, namespace="add_product").get("variant_add_key_answer"))
def get_variant_add_key_answer(message):
    try:
        product_bot.get_variant_add_key_answer(message)
    except:
        print(traceback.format_exc())

@app.message_handler(func=lambda message: session_manager.get_user_session(message.chat.id, namespace="add_product").get("variants_stock_values"))
def get_variants_stock_values(message):
    try:
        product_bot.get_variants_stock_values(message)
    except:
        print(traceback.format_exc())


@app.message_handler(func=lambda message: session_manager.get_user_session(message.chat.id, namespace="add_product").get("add_another_variant_key"))
def add_another_variant_key(message):
    try:
        product_bot.get_add_another_variant_key(message)
    except:
        print(traceback.format_exc())


@app.message_handler(func=lambda message: session_manager.get_user_session(message.chat.id, namespace="add_product").get("get_description"))
def add_product_get_description(message):
    try:
        session = session_manager.get_user_session(message.chat.id, namespace="add_product")
        
        # اگر از حالت واریانت آمده‌ایم، موجودی قبلاً تنظیم شده

        if not session.get("no_variant"):
            # حالت واریانت - فقط توضیحات را دریافت کن
            description = None if message.text == t(message, "no_description") else message.text
            print(description)
            session["get_description"] = False
            session["get_attribute"] = True
            session["get_description_d"] = description

            session_manager.set_user_session(message.chat.id, session, namespace="add_product")

        else:
            # حالت بدون واریانت - ابتدا موجودی را دریافت کن
            stock_str = message.text.strip()
            if not stock_str.isdigit():
                app.send_message(message.chat.id, t(message, "balance_not_integer"))
                return
                
            stock = int(stock_str)
            session["get_stock_d"] = stock
            session["get_description"] = False
            session["get_attribute"] = True

            session_manager.set_user_session(message.chat.id, session, namespace="add_product")

            markup = send_menu(message, [t(message, "no_description")], "main menu", [t(message, "cancel_action")]) 
            app.send_message(message.chat.id, t(message, "enter_description"), reply_markup=markup)
            
    except ValueError:
        app.send_message(message.chat.id, t(message, "balance_not_integer"))
    except Exception:
        print(traceback.format_exc())


@app.message_handler(func=lambda message: session_manager.get_user_session(message.chat.id, namespace="add_product").get("get_attribute"))
def add_product_get_attributes(message):
    try:
        product_bot.get_description(message)
    except Exception:
        print(traceback.format_exc())

@app.message_handler(func=lambda message: session_manager.get_user_session(message.chat.id, namespace="add_product").get("get_more_attributes"))
def add_product_get_more_attributes(message):
    try:
        product_bot.get_product_attributes(message)
    except Exception:
        print(traceback.format_exc())

@app.message_handler(func=lambda message: session_manager.get_user_session(message.chat.id, namespace="add_product").get("get_main_image"))
def add_product_finish_attributes(message):
    try:
        product_bot.handle_finish_attributes(message)
    except Exception:
        print(traceback.format_exc())

@app.message_handler(func=lambda message: session_manager.get_user_session(message.chat.id, namespace="add_product").get("get_additional_images"), content_types=["photo", "text"])
def add_product_get_additional_images(message):
    try:
        product_bot.get_main_image(message)
    except Exception:
        print(traceback.format_exc())

@app.message_handler(func=lambda message: session_manager.get_user_session(message.chat.id, namespace="add_product").get("process_accomplished"), content_types=["photo", "text"])
def add_product_process_accomplished(message):
    try:
        product_bot.get_additional_images(message)
        session = session_manager.get_user_session(message.chat.id, namespace="add_product")
    except Exception:
        print(traceback.format_exc())



@app.message_handler(func=lambda message: session_manager.get_user_session(message.chat.id, namespace="add_product").get("process_getout"), content_types=["photo"])
def add_product_process_getout(message):
    try:
        product_bot.get_additional_images(message)
        session = session_manager.get_user_session(message.chat.id, namespace="add_product")

        session2 = session_manager.get_user_session(message.chat.id, namespace="menu")
        session2['add_product'] = False
        session_manager.set_user_session(message.chat.id, session2, namespace="menu")

        print(session.get("code"))
        product_obj = Product.objects.get(code=session.get("code"))
        attributes = product_obj.attributes.all()
        product_handler = ProductHandler(app, product_obj, current_site, attributes=attributes)
        product_handler.send_product_message(message.chat.id, buttons=False)

        session_manager.reset_user_session(message.chat.id, namespace="add_product")
        product(message)
    except:
        print("*" * 20)
        print(traceback.format_exc())


#####################################    REMOVE PRODUCT    #####################################

@app.message_handler(func=lambda message: session_manager.get_user_session(message.chat.id, namespace="delete_product").get("enter_product_code_to_delete"))
def enter_product_code_to_delete(message):
    try:
        product_bot.delete(message)
    except Exception:
        print(traceback.format_exc())

def remove_product(message):
    """Start the product deletion process (only own store)."""
    try:
        if subscription.subscription_offer(message):
            store = get_user_store(message)
            if store:
                
                if not store.product_store.exists():
                    # Store has no products
                    app.send_message(message.chat.id, t(message, "no_products_to_delete"))
                    return
                markup = send_menu(message, [], "deletion", [t(message, "cancel_action")])
                app.send_message(message.chat.id, t(message, "enter_product_code_to_delete"), reply_markup=markup)
                session_manager.set_user_session(message.chat.id, {"enter_product_code_to_delete": True}, namespace="delete_product")
                session = session_manager.get_user_session(message.chat.id, namespace="menu")
                session["delete_product"] = True
                session_manager.set_user_session(message.chat.id, session, namespace="menu")
            else:
                app.send_message(message.chat.id, t(message, "not_a_seller_delete_product"))
    except Exception:
        print(traceback.format_exc())

@app.message_handler(func=lambda message: session_manager.get_user_session(message.chat.id, namespace="delete_product").get("delete_product_confirm"))
def delete_product_confirm(message):
    try:
        product_bot.delete_confirm(message)
        product(message)
    except Exception:
        print(traceback.format_exc())


#####################################    DEACTIVATE PRODUCT    #####################################

@app.message_handler(func=lambda message: session_manager.get_user_session(message.chat.id, namespace="menu").get("deavtivate_product"))
def enter_product_code_to_deactivate(message):
    try:
        product_bot.deactivate(message)
    except Exception:
        print(traceback.format_exc())


@app.message_handler(func=lambda message: message.text == t(message, "menu_deactivate") and session_manager.get_user_session(message.chat.id, namespace="menu")["product"])
def deactivate_product(message):
    try:
        if subscription.subscription_offer(message):
            profile = ProfileModel.objects.get(tel_id=message.from_user.id)
            if profile.seller_mode:
                if not get_user_store(message).product_store.exists():
                    # Store has no products
                    app.send_message(message.chat.id, t(message, "no_products_to_toggle"))
                    return
                # product_bot.set_state(message.chat.id, product_bot.ProductState.DEACTIVATE)
                session = session_manager.get_user_session(message.chat.id, namespace="menu")
                session["deavtivate_product"] = True
                session_manager.set_user_session(message.chat.id, session, namespace="menu")
                markup = send_menu(message, [], "deactivation", [t(message, "cancel_action")])
                app.send_message(message.chat.id, t(message, "enter_product_code_to_deactivate"), reply_markup=markup)
            else:
                app.send_message(message.chat.id, t(message, "not_a_seller_deactivate"))
    except Exception as e:
        custom_error = f"Error in deactivate handler: {e}\n\n{traceback.format_exc()}"
        print(custom_error)


@app.message_handler(func=lambda message: session_manager.get_user_session(message.chat.id, namespace="deactivate_product").get("deactivate_product_confirm"))
def deactivate_product_confirm(message):
    try:
        session = session_manager.get_user_session(message.chat.id, namespace="menu")
        session["deactivate_product_confirm"] = False
        session_manager.set_user_session(message.chat.id, session, namespace="menu")
        product_bot.deactivate_confirm(message)
        product(message)
    except Exception:
        print(traceback.format_exc())

##################################### LIST OF PRODUCTS #####################################

@app.message_handler(func=lambda message: message.text == t(message, "my_products_list"))
def product_list_method(message):
    try:
        if subscription.subscription_offer(message):
            profile = ProfileModel.objects.get(tel_id=message.from_user.id)
            if profile.seller_mode:
                if not get_user_store(message).product_store.exists():
                    # Store has no products
                    app.send_message(message.chat.id, t(message, "no_products_to_represent"))
                    return
                session = session_manager.get_user_session(message.chat.id, namespace="menu")
                session["product_list"] = True
                session["product_list_method"] = True
                session_manager.set_user_session(message.chat.id, session, namespace="menu")
                markup = send_menu(message, ["Excel", "PDF", t(message, "view_here")], "product_list_method", [t(message, "cancel_action")])
                app.send_message(message.chat.id, t(message, "view_products_format"), reply_markup=markup)
    except:
        print(traceback.format_exc())


def product_list_excel(message):
    """تابع اصلی برای صادرات محصولات"""
    exporter = AdvancedProductExporter()
    return exporter.export_products_to_excel(message, use_cache=True)


@app.message_handler(func=lambda message: message.text == "Excel" and session_manager.get_user_session(message.chat.id, namespace="menu").get("product_list_method"))
def handle_export_products(message):
    try:
        result = product_list_excel(message)
        
        if 'error' in result:
            app.reply_to(message, f"❌ {result['error']}")
        else:
            cache_info = " (from cache)" if result.get('from_cache') else ""
            user_lang = result.get('user_lang', 'en')
            
            # استفاده از تابع t برای ترجمه caption
            caption = t(message, 'product_export_caption', 
                       store_name=result['store_name'],
                       total_products=result['metadata']['total_products'],
                       total_variants=result['metadata']['total_variants'],
                       total_stock_value=result['metadata']['total_stock_value'])
            
            if cache_info:
                caption += f" {cache_info}"
            
            app.send_document(
                message.chat.id,
                result['file_buffer'],
                visible_file_name=result['filename'],
                caption=caption
            )
            
    except Exception as e:
        print(f"Error in export handler: {traceback.format_exc()}")
        app.reply_to(message, "❌ خطایی در ارسال فایل رخ داد")

##################################### END OF PRODUCT #####################################

##################################### CATEGORY #####################################

@app.message_handler(func=lambda message: message.text == t(message, "category"))
def category(message):
    if subscription.subscription_offer(message):
        profile = ProfileModel.objects.get(tel_id=message.from_user.id)
        if profile.seller_mode:
            home_menue = ["🏡"]
            session_manager.reset_user_session(message.chat.id, namespace="menu")
            session = session_manager.get_user_session(message.chat.id, namespace="menu")
            session['product'] = False
            session['category'] = True
            session_manager.set_user_session(message.chat.id, session, namespace="menu")
            markup = send_menu(message, [t(message, "menu_add"), t(message, "menu_delete"), t(message, "menu_deactivate"), t(message, "edit")], "category", home_menue)
            app.send_message(message.chat.id, t(message, "what_action_on_category"), reply_markup=markup)

        else:
            app.send_message(message.chat.id, t(message, "not_a_seller_edit_categories"))


@app.message_handler(func=lambda m: m.text == t(m, "menu_delete"))
def delete_handler(message):
    session = session_manager.get_user_session(message.chat.id, namespace="menu")
    session["menu_delete"] = True
    session_manager.set_user_session(message.chat.id, session, namespace="menu")

    if session.get("category"):
        # Category deletion

        category_class = CategoryClass()
        category_class.handle_category(message)

    elif session.get("product"):
        # Product deletion
        remove_product(message)



@app.message_handler(func=lambda message: message.text.lower() in [i.lower() for i in Category.objects.annotate(
    lower_title=Lower('title')).filter(lower_title=message.text.lower(), status=True).values_list('title', flat=True)]
    and not session_manager.get_user_session(message.chat.id, namespace="menu").get("add_product"))
def subcategory(message):
    category_class = CategoryClass()
    category_class.handle_subcategory(message)




@app.message_handler(func=lambda message: session_manager.get_user_session(message.chat.id, namespace="menu").get("category") and
                    session_manager.get_user_session(message.chat.id, namespace="menu").get("menu_add"))
def get_new_category(message):
    try:
        session = session_manager.get_user_session(message.chat.id, namespace="menu")
        profile = ProfileModel.objects.get(tel_id=message.chat.id)
        store = Store.objects.get(owner=profile) if profile.seller_mode else profile.server_store

        # Decide parent
        parent_title = session.get("parent_for_new")
        parent = None
        if parent_title:
            parent = Category.objects.filter(title__iexact=parent_title, status=True).first()

        # Create category
        cat = Category.objects.create(
            title=message.text,
            slug=message.text,
            status=True,
            parent=parent,
            store=store
        )

        # Update session (stay in same parent unless user navigates elsewhere)
        if parent:
            session["current_menu"] = parent.title
            session["parent_for_new"] = parent.title   # 🔑 keep parent locked
        else:
            session["current_menu"] = None
            session["parent_for_new"] = None

        session["get_new_category"] = False
        session_manager.set_user_session(message.chat.id, session, namespace="menu")

        # Refresh menu
        category_class = CategoryClass()
        if parent:
            message.text = parent.title
            category_class.handle_subcategory(message)
        else:
            category_class.handle_category(message)

    except Exception:
        print(traceback.format_exc())



@app.message_handler(func=lambda message: message.text == t(message, "menu_categories"))
def category_client(message):
    category_class = CategoryClass()
    category_class.handle_category(message)


@app.message_handler(func=lambda message: message.text == t(message, "delete_category_and_subcategories"))
def delete_cat_subcat(message):
    try:
        category_class = CategoryClass()
        category_class.delete_sure(message)
    except Exception as e:
        print(traceback.format_exc())

@app.message_handler(func=lambda message: message.text == t(message, "yes_im_sure"))
def cat_delete(message):
    try:
        session = session_manager.get_user_session(message.chat.id, namespace="menu")
        if session_manager.get_user_session(message.chat.id, namespace="menu").get("delete_sure"):
            cat = Category.objects.get(title__iexact=session.get("current_menu"), status=True)
            parent = cat.get_parents()
            cat.delete()
            category_class = CategoryClass()
            if not cat.store.categories.exists():
                category(message)
                return
            if parent:
                if parent[0].get_all_subcategories():
                    message.text = parent[0].title
                else:
                    message.text = parent[1].title
                category_class.handle_subcategory(message)
            else:
                category_class.handle_category(message)
        elif session_manager.get_user_session(message.chat.id, namespace="menu").get("deactivate_category_sure"):
            cat = Category.objects.get(title__iexact=session.get("current_menu"), status=True)
            cat.status = False
            cat.save()
            parent = cat.get_parents()
            if not [c for c in cat.store.categories.all() if c.status]:
                category(message)
                return
            category_class = CategoryClass()
            if parent:
                if [par for par in parent[0].get_all_subcategories() if par.status]:
                    message.text = parent[0].title
                else:
                    message.text = parent[1].title
                category_class.handle_subcategory(message)
            else:
                category_class.handle_category(message)
        
        session["menu_delete"] = False
        session["delete_sure"] = False
        session_manager.set_user_session(message.chat.id, session, namespace="menu")

    except Exception as e:
        print(traceback.format_exc())


@app.message_handler(func=lambda message: message.text == t(message, "menu_deactivate") and session_manager.get_user_session(message.chat.id, namespace="menu").get("category"))
def deactivate_category(message):
    try:
        if subscription.subscription_offer(message):
            profile = ProfileModel.objects.get(tel_id=message.from_user.id)
            if profile.seller_mode:
                session = session_manager.get_user_session(message.chat.id, namespace="menu")
                session["category_deactivate"] = True
                session_manager.set_user_session(message.chat.id, session, namespace="menu")
                if not Category.objects.filter(store=get_user_store(message)).exists():
                    app.send_message(message.chat.id, t(message, "no_categories_for_toggle"))
                    return
                category_class = CategoryClass()
                category_class.handle_category(message)
            else:
                app.send_message(message.chat.id, t(message, "not_a_seller_deactivate"))
    except Exception as e:
        custom_error = f"Error in deactivate handler: {e}\n\n{traceback.format_exc()}"
        print(custom_error)


@app.message_handler(func=lambda message: message.text in [t(message, "deactivate_category"), t(message, "activate_category")])
def confirm_deactivate_category(message):
    category_class = CategoryClass()
    category_class.deactivate_category_sure(message)

product_bot = ProductBot(app)
product_bot.register_handle_finish_attributes()


##################################### END CATEGROY #####################################

# hadling any unralted message
@app.message_handler(func=lambda message: app.get_state(user_id=message.from_user.id, chat_id=message.chat.id) is None)
def handle_message(message):
    if subscription.subscription_offer(message):
        app.send_message(message.chat.id, t(message, "command_not_found"))



# Handling the callback query when the 'answer' button is clicked
@app.callback_query_handler(func=lambda call: call.data == "پاسخ")
def answer(call):
    try:
        pattern = r"Recived a message from \d+"
        clean_text = BeautifulSoup(call.message.text, "html.parser").get_text()
        print( re.findall(pattern=pattern, string=clean_text))
        user = re.findall(pattern=pattern, string=clean_text)[0].split()[4]

        app.send_message(chat_id=call.message.chat.id, text=f"Send your answer to <code>{user}</code>:",
                         reply_markup=types.ForceReply(), parse_mode="HTML")

        app.set_state(user_id=call.from_user.id, state=Support.respond, chat_id=call.message.chat.id)

    except Exception as e:
        error_message = traceback.format_exc()
        print(f"your error is: {error_message}")


# Handling the support agent's reply message which is saved in 'Support.respond' state
@app.message_handler(state=Support.respond,
                     func=lambda message: message.reply_to_message.text.startswith("Send your answer to"))
def answer_text(message):
    try:
        pattern = r"Send your answer to \d+"
        clean_text = BeautifulSoup(message.reply_to_message.text, "html.parser").get_text()
        user = int(re.findall(pattern=pattern, string=clean_text)[0].split()[4])

        try:
            user_message = texts[user]
            app.send_message(chat_id=user,
                             text=f"Your message:\n<i>{escape_special_characters(user_message)}</i>\n\nSupport answer:\n<b>{escape_special_characters(message.text)}</b>",
                             parse_mode="HTML")
            app.send_message(chat_id=message.chat.id, text="پیام شما ارسال شد!")

            del texts[user]
            app.delete_state(user_id=message.from_user.id, chat_id=message.chat.id)

        except:
            app.send_message(chat_id=user, text=f"Support answer:\n<b>{escape_special_characters(message.text)}</b>",
                             parse_mode="HTML")
            app.send_message(chat_id=message.chat.id, text="پاسخ شما ارسال شد!")

            app.delete_state(user_id=message.from_user.id, chat_id=message.chat.id)

    except Exception as e:
        app.send_message(chat_id=message.chat.id, text=f"Something goes wrong...\n\nException:\n<code>{e}</code>",
                         parse_mode="HTML")

    markup = send_menu(message, main_menu, "main_menu", extra_buttons)
    app.send_message(message.chat.id, "لطفا یکی از گزینه های زیر را انتخاب کنید:", reply_markup=markup)


@app.callback_query_handler(func=lambda call: call.data == "پایان مکالمه")
def terminate_chat(call):
    if subscription.subscription_offer(call.message):
        try:
            app.delete_state(user_id=call.from_user.id, chat_id=call.message.chat.id)
            app.send_message(chat_id=call.message.chat.id, text=f"مکالمه شما پایان یافت.")
        except Exception as e:
            error_message = traceback.format_exc()
            print(f"your error is: {error_message}")


##################################

#####################################################################################################
# Functions for specific actions


# show balance
def show_balance(message):
    # Example: Fetch and send user balance
    try:
        if subscription.subscription_offer(message):
            user_id = message.from_user.id
            balance = ProfileModel.objects.get(tel_id=user_id).credit
            formatted_balance = "{:,.2f}".format(float(balance))
            app.send_message(message.chat.id, t(message, "user_balance", formatted_balance=formatted_balance))
    except:
        app.send_message(message.chat.id, traceback.format_exc())
    

def ask_for_product_code(message):
    if subscription.subscription_offer(message):
        app.send_message(message.chat.id, "لطفاً کد کالای مورد نظر را وارد کنید:")
        app.set_state(user_id=message.from_user.id, state=Support.code, chat_id=message.chat.id)


def send_website_link(message):
    """Send a button that opens the website in a browser."""
    if subscription.subscription_offer(message):
        # Create an Inline Keyboard with a button linking to the website
        markup = types.InlineKeyboardMarkup()
        website_button = types.InlineKeyboardButton("بازدید از سایت", url=current_site)
        markup.add(website_button)

        # Send a message with the inline keyboard
        app.send_message(
            message.chat.id,
            "برای بازدید از سایت، دکمه زیر را فشار دهید:",
            reply_markup=markup
        )


@app.callback_query_handler(func=lambda call: call.data == 'check_website_subscription')
def check_website_subscription(call):
    if subscription.subscription_offer(call.message):
        if not ProfileModel.objects.filter(telegram=call.from_user.username).exists():
            # signup process

            app.send_message(call.message.chat.id,
                             "برای خرید و ارسال کالا باید اطلاعات بیشتری (مثل آدرس) از شما داشته باشیم.\n\nابتدا باید حساب کاربری خود را بسازید:")
            home_menue = ["🏡"]

            send_menu(call.message, extra_buttons, "create_account", home_menue)
        else:
            # Buy Process
            pass



# email validation
def is_valid_email(email):
    print(re.match(r'^[a-z]+$', 'test'))
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(email_pattern, email):
        return True, 'حالا یه نام کاربری برای خودت انتخاب کن:'
    else:
        return False, "یه جایی این آدرس ایمیلی که نوشتی ایراد داره به نظرم! بگرد پیداش کن درستش کن دوباره برام بنویسش:"


# گرفتن آدرس ایمیل
def pick_email(message):
    try:
        email = message.text

        is_valid, validation_message = is_valid_email(email)  # Assign directly to validation_message

        if email in [item['email'] for item in User.objects.values("email")]:
            app.send_message(message.chat.id,
                             "قبل تر از شما کسی با این ایمیل حساب کاربری افتتاح کرده است! می خوای با یه ایمیل دیگه ات امتحان کن:")
            app.register_next_step_handler(message, pick_email)  # Prompt again for email
        else:
            if is_valid:
                username = message.from_user.username
                if username in [item['username'] for item in User.objects.values("username")] + [item['telegram'] for
                                                                                                 item in
                                                                                                 ProfileModel.objects.values(
                                                                                                         "telegram")] + [
                    item['tel_id'] for item in ProfileModel.objects.values("tel_id")]:
                    app.send_message(message.chat.id, validation_message)  # This now uses validation_message correctly
                    app.register_next_step_handler(message, pick_username, email)  # Proceed to username prompt
                else:
                    app.send_message(message.chat.id,
                                     "نام کاربری شما همان ID تلگرام شماست!\n\n حالا یه رمز عبور هشت رقمی شامل حروف برزگ و کوچک عدد و یک علامت‌ برای خودت انتخاب کن:")
                    app.register_next_step_handler(message, pick_password, email, username)
            else:
                app.send_message(message.chat.id, validation_message)  # Re-prompt for a valid email
                app.register_next_step_handler(message, pick_email)  # Prompt again for email
    except Exception as e:
        app.send_message(chat_id=message.chat.id, text=f"the error is: {e}")


# دریافت نام کاربری
def pick_username(message, email):
    try:
        username = message.text
        is_valid, validation_message = validate_username(username)  # Validation message is now separate from `message`

        # Send validation message
        app.send_message(message.chat.id, validation_message)

        if is_valid:
            # Check if username already exists
            if username in [item['username'] for item in User.objects.values("username")]:
                app.send_message(message.chat.id,
                                 "متاسفانه نام کاربری که انتخاب کردی از قبل انتخاب شده لطفا یکی دیگه رو امتحان کن:")
                app.register_next_step_handler(message, pick_username, email)
            else:
                app.send_message(message.chat.id,
                                 "عالیه! حالا یه رمز عبور هشت رقمی شامل حروف برزگ و کوچک عدد و یکی از علامت‌ها برای خودت انتخاب کن:")
                app.register_next_step_handler(message, pick_password, email, username)
        else:
            # If the username is invalid, re-prompt the user
            app.register_next_step_handler(message, pick_username, email)

    except Exception as e:
        app.send_message(chat_id=message.chat.id, text=f"the error is: {e}")


# تعیین رمز عبور
def pick_password(message, email, username):
    try:
        password = message.text
        is_valid, validation_message = validate_password(password)

        # Send validation message
        app.send_message(message.chat.id, validation_message)

        # If password is valid, proceed with registration
        if is_valid:

            app.send_message(message.chat.id,
                             "دمت گرم! حالا یه بار دیگه رمزت رو برام بزن تا تاییدش کنم و این بشه رمز عبورت:")
            app.register_next_step_handler(message, pick_password2, email, username, password)


        # If password is not valid, ask for a new one
        else:
            app.register_next_step_handler(message, pick_password, email, username)

    except Exception as e:
        app.send_message(chat_id=message.chat.id, text=f"the error is: {e}")


# تایید رمز
def pick_password2(message, email, username, password, current_site=current_site):
    if subscription.subscription_offer(message):
        try:
            password2 = message.text

            if password2 == password:
                User = get_user_model()

                special_user_date = timezone.now() + timedelta(days=5)

                user = User.objects.create(
                    username=username,
                    email=email,
                    password=make_password(password),
                    special_user=special_user_date,
                    is_active=False
                )

                # ساخت پروفایل
                profile = ProfileModel.objects.get(tel_id=message.from_user.id)

                profile.user = user

                # دانلود و تنظیم عکس نمایه از تلگرام
                download_profile_photo(message.from_user.id, profile)

                mail_subject = 'Activation link has been sent to your email id'
                telegram_activation_link = f"https://t.me/{BOT_ID}_bot?start=activate_{urlsafe_base64_encode(force_bytes(user.pk))}_{generate_token.make_token(user)}"

                message_content = render_to_string('registration/acc_active_email.html', {
                    'user': user,
                    'domain': current_site[8:],
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': generate_token.make_token(user),
                    'telegram': True,
                    'telegram_activation_link': telegram_activation_link
                })

                email = EmailMessage(
                    mail_subject, message_content, to=[email]
                )
                email.content_subtype = "html"
                email.send()

                app.send_message(message.chat.id,
                                 "دوست عزیزم یک ایمیل از طرف شرکت اینتلیوم برای شما ارسال شده است که حاوی لینک فعالسازی حساب شماست لطفا روی آن کلیک کنید.")
            else:
                app.send_message(message.chat.id, "تایید رمز عبور با رمز عبوری که از قبل وارد کردید تطابق ندارد.")
                app.register_next_step_handler(message, pick_password2, email, username, password)
        except Exception as e:
            app.send_message(chat_id=message.chat.id, text=f"the error is: {e}")


# تابع برای پرسیدن خط دوم آدرس
def pick_address_line2(message):
    try:
        shipping_line1 = message.text
        app.send_message(message.chat.id, "لطفاً خط دوم آدرس را وارد کنید:")
        app.register_next_step_handler(message, pick_country, shipping_line1)
    except Exception as e:
        app.send_message(chat_id=message.chat.id, text=f"خطا: {e}")


# تابع برای پرسیدن کشور
def pick_country(message, shipping_line1):
    try:
        shipping_line2 = message.text
        app.send_message(message.chat.id, "لطفاً کشور خود را وارد کنید:")
        app.register_next_step_handler(message, pick_province, shipping_line1, shipping_line2)
    except Exception as e:
        app.send_message(chat_id=message.chat.id, text=f"خطا: {e}")


# تابع برای پرسیدن شهر
def pick_province(message, shipping_line1, shipping_line2):
    try:
        shipping_country = message.text
        app.send_message(message.chat.id, "لطفاً استان خود را وارد کنید:")
        app.register_next_step_handler(message, pick_city, shipping_line1, shipping_line2, shipping_country)
    except Exception as e:
        app.send_message(chat_id=message.chat.id, text=f"خطا: {e}")


# تابع برای پرسیدن استان
def pick_city(message, shipping_line1, shipping_line2, shipping_country):
    try:
        shipping_province = message.text
        app.send_message(message.chat.id, "لطفاً شهر خود را وارد کنید:")
        app.register_next_step_handler(message, pick_zip, shipping_line1, shipping_line2, shipping_country,
                                       shipping_province)
    except Exception as e:
        app.send_message(chat_id=message.chat.id, text=f"خطا: {e}")


# تابع برای پرسیدن کد پستی
def pick_zip(message, shipping_line1, shipping_line2, shipping_country, shipping_province):
    try:
        shipping_city = message.text
        app.send_message(message.chat.id, "لطفاً کد پستی خود را وارد کنید:")
        app.register_next_step_handler(message, pick_phone, shipping_line1, shipping_line2, shipping_country,
                                       shipping_province, shipping_city)
    except Exception as e:
        app.send_message(chat_id=message.chat.id, text=f"خطا: {e}")


# تابع برای پرسیدن شماره تلفن
def pick_phone(message, shipping_line1, shipping_line2, shipping_country, shipping_province, shipping_city):
    try:
        shipping_zip = message.text
        app.send_message(message.chat.id, "لطفاً شماره تلفن منزل خود را وارد کنید:")
        app.register_next_step_handler(message, save_shipping_address, shipping_line1, shipping_line2, shipping_country,
                                       shipping_province, shipping_city, shipping_zip)
    except Exception as e:
        app.send_message(chat_id=message.chat.id, text=f"خطا: {e}")


# تابع برای ذخیره اطلاعات آدرس
def save_shipping_address(message, shipping_line1, shipping_line2, shipping_country, shipping_province, shipping_city,
                          shipping_zip):
    try:
        shipping_home_phone = message.text
        profile = ProfileModel.objects.get(telegram=message.from_user.username)

        # ذخیره آدرس در مدل pick_phone
        profile.shipping_line1 = shipping_line1
        profile.shipping_line2 = shipping_line2
        profile.shipping_country = shipping_country
        profile.shipping_city = shipping_city
        profile.shipping_province = shipping_province
        profile.shipping_zip = shipping_zip
        profile.shipping_home_phone = shipping_home_phone
        profile.save()

        app.send_message(message.chat.id, "آدرس شما با موفقیت ثبت شد!")
    except Exception as e:
        app.send_message(chat_id=message.chat.id, text=f"خطا: {e}")


app.add_custom_filter(custom_filters.StateFilter(app))
