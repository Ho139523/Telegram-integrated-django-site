from utils.variables.TOKEN import TOKEN, BOT_ID
import requests
import subprocess
import re
from telebot import TeleBot
from telebot.types import Message
from telebot.storage import StateMemoryStorage
from accounts.models import ProfileModel, Address
from products.models import Product, Category, ProductImage, ProductAttribute, Store, ProductVariant
from payment.models import Transaction, Sale, Cart, CartItem
import os
from django.conf import settings
import requests
from django.core.files.base import ContentFile
import json
import urllib.parse
import base64
import uuid
from django.core.cache import cache
from utils.variables.translate import translations
from django.db.models.functions import Lower
import itertools
import traceback
import re
from telebot.types import Message
from products.models import (
    Product, ProductAttribute, ProductImage,
    ProductVariant, ProductOption, ProductOptionValue
)
from accounts.models import ProfileModel
from products.models import Store, Category
from django.db.models import Q

# send_product_message function
from telebot import types


# bot settings
from telebot.storage import StateMemoryStorage
state_storage = StateMemoryStorage()
app = TeleBot(token=TOKEN, state_storage=state_storage)


from telbot.sessions import CartSessionManager, RedisStateManager, SessionManager

# Access shared user_sessions
from telbot.sessions import session_manager

from utils.telbot.variables import *
import os
import requests
from django.conf import settings

from utils.telbot.variables import home_menu

from PIL import Image, ImageDraw, ImageFont
from django.utils import timezone

from django.conf import settings as sett


from utils.funcs.geonames_address import get_country_choices, get_province_choices, get_city_choices


def t(msg, key, **kwargs):
    try:        
        if isinstance(msg, types.Message):
            message = msg
        else:
            message = msg.message

        lang = ProfileModel.objects.get(tel_id=message.chat.id).lang
        text = translations.get(key, {}).get(lang, translations[key]["en"])
        
        # جایگذاری متغیرها
        if kwargs:
            text = text.format(**kwargs)
        return text
    except Exception as e:
        print(e)




def get_tunnel_password():
    try:
        result = subprocess.run(
            ["curl", "-s", "https://loca.lt/mytunnelpassword"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            password = result.stdout.strip()  # حذف فاصله‌ها و خط‌های اضافی
            return password
        else:
            print("Error fetching password:", result.stderr)
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None



# Getting website address and webhook

def get_current_webhook(TOKEN=TOKEN):
    bot_token = TOKEN  # Ensure you have your bot token in Django settings
    response = requests.get(f'https://api.telegram.org/bot{bot_token}/getWebhookInfo')

    if response.status_code == 200:
        webhook_info = response.json()

        # Check if there's a URL set for the webhook
        if webhook_info.get('ok') and webhook_info['result'].get('url'):
            return webhook_info['result']['url']
        else:
            return "No webhook URL set."
    else:
        return "Failed to retrieve webhook info."

def get_current_site(TOKEN=TOKEN):
    bot_token = TOKEN  # Ensure you have your bot token in Django settings
    response = requests.get(f'https://api.telegram.org/bot{bot_token}/getWebhookInfo')

    if response.status_code == 200:
        site_info = response.json()

        # Check if there's a URL set for the webhook
        if site_info.get('ok') and site_info['result'].get('url'):
            return site_info['result']['url'][:-9]
        else:
            return "No site URL set."
    else:
        return "Failed to retrieve site info."


# بررسی معتبر بودن رمز عبور
def validate_password(password):
    # شرط طول رمز عبور حداقل ۸ کاراکتر
    if len(password) < 8:
        return False, "رمز عبور باید حداقل ۸ کاراکتر باشد."

    # شرط حروف کوچک
    if not re.search(r"[a-z]", password):
        return False, "رمز عبور باید حداقل شامل یک حرف کوچک باشد."

    # شرط حروف بزرگ
    if not re.search(r"[A-Z]", password):
        return False, "رمز عبور باید حداقل شامل یک حرف بزرگ باشد."

    # شرط عدد
    if not re.search(r"[0-9]", password):
        return False, "رمز عبور باید حداقل شامل یک عدد باشد."

    # شرط علامت‌ها
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "رمز عبور باید حداقل شامل یک علامت باشد."

    # اگر همه شرایط برقرار بود
    return True, "رمز عبورت خوبه."


def validate_username(username):
    # Check length
    if len(username) < 5 or len(username) > 32:
        return False, "طول نام کاربری باید بین 5 تا 32 حرف باشد."

    # Check for allowed characters and disallow "."
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False, "نام کاربری تنها شامل حروف، عدد و underline باشد."

    # Check for presence of "."
    if "." in username:
        return False, "نام کاربری نمی تواند شامل «.» باشد."

    return True, "این نام کاربری خوبه"



############################  SEND PRODUCT MESSAGE  ############################

class UserOrderManager:
    """مدیریت تعداد سفارش‌های هر کاربر"""
    def __init__(self):
        self.user_counts = {}

    def increase(self, chat_id):
        self.user_counts[chat_id] = self.user_counts.get(chat_id, 0) + 1

    def decrease(self, chat_id):
        if self.user_counts.get(chat_id, 0) > 1:
            self.user_counts[chat_id] -= 1
        else:
            self.user_counts.pop(chat_id, None)

    def get_count(self, chat_id):
        return self.user_counts.get(chat_id, 0)





# نحوه استفاده:
# product_handler = ProductHandler(app, product, current_site)
# product_handler.send_product_message(chat_id)

############################  PAGINATION  ############################

import math
import json
import redis

class InlineKeyboardPaginator:
    def __init__(
            self,
            user_id,
            items=None,
            per_page=10,
            row_size=3,
            remember_last_page=False,
            redis_host="localhost",
            redis_port=6379
    ):
        """
        :param user_id: آیدی کاربر
        :param items: لیست آیتم‌ها (مثل کشورها) – اگر None باشد از Redis بارگذاری می‌شود
        :param per_page: تعداد آیتم در هر صفحه
        :param row_size: تعداد دکمه در هر ردیف
        :param remember_last_page: اگر True باشد، صفحه‌ی آخر کاربر ذخیره می‌شود
        """
        self.user_id = user_id
        self.per_page = per_page
        self.row_size = row_size
        self.remember_last_page = remember_last_page
        self.redis = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)

        if items is not None:
            self.items = items
            self.total_pages = max(1, math.ceil(len(items) / per_page))
            self._save_state(1 if not remember_last_page else self._get_saved_page(), items)
        else:
            self._load_state()

    def _get_key(self):
        return f"paginator:{self.user_id}"

    def _save_state(self, page, items):
        """ذخیره وضعیت در Redis"""
        data = {
            "items": items,
            "page": page,
            "per_page": self.per_page,
            "row_size": self.row_size,
            "remember_last_page": self.remember_last_page
        }
        self.redis.set(self._get_key(), json.dumps(data))

    def _load_state(self):
        """لود وضعیت از Redis"""
        data = self.redis.get(self._get_key())
        if not data:
            raise ValueError(f"No paginator state found for user_id={self.user_id}")
        data = json.loads(data)
        self.items = data["items"]
        self.per_page = data.get("per_page", self.per_page)
        self.row_size = data.get("row_size", self.row_size)
        self.remember_last_page = data.get("remember_last_page", self.remember_last_page)
        self.total_pages = max(1, math.ceil(len(self.items) / self.per_page))
        self.set_page(data.get("page", 1))

    def _get_saved_page(self):
        """بررسی صفحه ذخیره شده (اگر وجود داشته باشد)"""
        data = self.redis.get(self._get_key())
        if data:
            data = json.loads(data)
            return data.get("page", 1)
        return 1

    def get_current_page(self):
        data = json.loads(self.redis.get(self._get_key()))
        return data.get("page", 1)

    def set_page(self, page: int):
        page = max(1, min(self.total_pages, page))
        data = json.loads(self.redis.get(self._get_key()))
        if self.remember_last_page:  # Only update saved page if this option is enabled
            data["page"] = page
        else:
            data["page"] = 1  # Always reset to 1 when user leaves
        self.redis.set(self._get_key(), json.dumps(data))

    def next_page(self):
        current = self.get_current_page()
        if current < self.total_pages:
            self.set_page(current + 1)

    def prev_page(self):
        current = self.get_current_page()
        if current > 1:
            self.set_page(current - 1)

    def get_buttons_for_sendmarkup(self):
        try:
            current_page = self.get_current_page()
            start = (current_page - 1) * self.per_page
            end = start + self.per_page
            current_items = self.items[start:end]

            buttons = {}
            button_layout = []

            row_count = 0
            for idx, item in enumerate(current_items, start=1):
                buttons[item] = {"callback_data": item, "index": idx}
                row_count += 1
                if row_count == self.row_size or idx == len(current_items):
                    button_layout.append(row_count)
                    row_count = 0


            if len(self.items) <= self.per_page:
                return buttons, button_layout

            control_buttons = []
            idx = len(buttons) + 1
            if current_page > 1:
                buttons["⬅️ قبلی"] = {"callback_data": "prev", "index": idx}
                control_buttons.append("⬅️ قبلی")
                idx += 1

            buttons[f"{current_page}/{self.total_pages}"] = {"callback_data": "current", "index": idx}
            control_buttons.append(f"{current_page}/{self.total_pages}")
            idx += 1

            if current_page < self.total_pages:
                buttons["بعدی ➡️"] = {"callback_data": "next", "index": idx}
                control_buttons.append("بعدی ➡️")

            button_layout.append(len(control_buttons))
            return buttons, button_layout
        except Exception as e:
            print(f"errors in class: {e}")

    @staticmethod
    def load_from_redis(user_id, redis_host="localhost", redis_port=6379):
        return InlineKeyboardPaginator(
            user_id=user_id,
            items=None,
            redis_host=redis_host,
            redis_port=redis_port
        )

############################  MEASURE PERFORMANCE  ############################

import time
import functools
from django.db import connection
from django.db import reset_queries

def measure_performance(func):
    """
    دکوراتور برای اندازه‌گیری سرعت اجرای توابع و تعداد کوئری‌های دیتابیس
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # زمان شروع
        start_time = time.time()
        
        # ریست کردن شمارشگر کوئری‌ها
        reset_queries()
        
        try:
            # اجرای تابع اصلی
            result = func(*args, **kwargs)
            
            # زمان پایان
            end_time = time.time()
            execution_time = end_time - start_time
            
            # تعداد کوئری‌های اجرا شده
            num_queries = len(connection.queries)
            
            # اطلاعات عملکرد
            performance_info = {
                'function_name': func.__name__,
                'execution_time': round(execution_time, 4),
                'num_queries': num_queries,
                'queries': connection.queries if num_queries > 0 else []
            }
            
            # چاپ اطلاعات
            print(f"🚀 PERFORMANCE REPORT - {func.__name__}")
            print(f"⏱️  Execution time: {execution_time:.4f} seconds")
            print(f"📊 Number of database queries: {num_queries}")
            
            if num_queries > 0:
                print("🔍 Queries executed:")
                for i, query in enumerate(connection.queries, 1):
                    print(f"   {i}. {query['sql']} (Time: {query['time']}s)")
            
            print("=" * 60)
            
            return result
            
        except Exception as e:
            # در صورت خطا هم زمان را اندازه بگیریم
            end_time = time.time()
            execution_time = end_time - start_time
            
            print(f"❌ ERROR in {func.__name__}")
            print(f"⏱️  Execution time before error: {execution_time:.4f} seconds")
            print(f"💥 Error: {e}")
            print("=" * 60)
            
            raise e
    
    return wrapper

def add_performance_monitoring_to_class(cls):
    """
    اضافه کردن مانیتورینگ عملکرد به همه متدهای یک کلاس

    استفاده:
    @add_performance_monitoring_to_class
    class ProductHandler:
    تمام متدهای شما به صورت خودکار مانیتور می‌شوند
    pass
    """
    for attr_name in dir(cls):
        attr = getattr(cls, attr_name)
        if callable(attr) and not attr_name.startswith('_'):
            setattr(cls, attr_name, measure_performance(attr))
    return cls


############################  SEND MARKUP  ############################

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot import types

class SendMarkup:
    def __init__(self, bot, chat_id, text=None, buttons=None, button_layout=None, handlers=None):
        from products.models import Product
        self.bot = bot
        self.chat_id = chat_id
        self.text = text
        self.buttons = buttons or {}
        self.button_layout = button_layout or []
        self.handlers = handlers or {}



    def generate_keyboard(self):
        """ 📌 ساخت کیبورد داینامیک بر اساس دکمه‌ها و چیدمان تعیین‌شده """
        markup = types.InlineKeyboardMarkup()
        button_list = []

        # اگر buttons یک لیست است (فرمت جدید)
        if isinstance(self.buttons, list):
            # مرتب‌سازی بر اساس ایندکس (عنصر سوم)
            sorted_buttons = sorted(self.buttons, key=lambda x: x[2])
            
            for text, callback_data, index in sorted_buttons:
                button_list.append(types.InlineKeyboardButton(text, callback_data=callback_data))
        
        # اگر buttons یک دیکشنری است (فرمت قدیم)
        else:
            # کد قبلی برای سازگاری با مکان‌های دیگر
            sorted_buttons = sorted(self.buttons.items(), key=lambda item: item[1]['index'] if isinstance(item[1], dict) else item[1][1])

            for text, button_data in sorted_buttons:
                if isinstance(button_data, dict):
                    if 'url' in button_data:
                        button_list.append(types.InlineKeyboardButton(
                            text,
                            url=button_data['url']
                        ))
                    else:
                        button_list.append(types.InlineKeyboardButton(
                            text,
                            callback_data=button_data.get('callback_data')
                        ))
                else:
                    callback_data, index = button_data
                    button_list.append(types.InlineKeyboardButton(text, callback_data=callback_data))

        # چیدمان دکمه‌ها بر اساس طرح‌بندی
        index = 0
        for row_size in self.button_layout:
            markup.row(*button_list[index:index + row_size])
            index += row_size

        return markup


    def send(self):
        """ 📌 ارسال پیام با دکمه‌ها """
        markup = self.generate_keyboard()
        self.bot.send_message(self.chat_id, self.text, reply_markup=markup, parse_mode="HTML")

    def edit(self, message_id):
        """ 📌 ویرایش پیام و به‌روزرسانی دکمه‌ها و متن """
        markup = self.generate_keyboard()
        self.bot.edit_message_text(
            chat_id=self.chat_id,
            message_id=message_id,
            text=self.text,
            reply_markup=markup,
            parse_mode="HTML"
        )



    def handle_callback(self, call):
        """ 📌 تابع مدیریت کلیک روی دکمه‌ها """
        callback_data = call.data  # مقدار دریافتی از دکمه کلیک شده
        if callback_data in self.handlers:
            self.handlers[callback_data](call)  # اجرای تابع مرتبط با دکمه


############################  CHECK SUBSCRIPTION  ############################

import logging
from utils.variables.CHANNELS import my_channels_with_atsign, my_channels_without_atsign

logger = logging.getLogger(__name__)

class SubscriptionClass:
    def __init__(self, bot: TeleBot):
        self.bot = bot
        self.my_channels_with_atsign = my_channels_with_atsign
        self.my_channels_without_atsign = my_channels_without_atsign
        self.current_site = 'https://intelleum.ir:8443'

    def handle_check_subscription(self, call: types.CallbackQuery):
        """✅ بررسی عضویت هنگام کلیک روی دکمه 'عضو شدم'"""
        chat_id = call.message.chat.id
        user_id = call.from_user.id



        # بررسی عضویت
        is_member = self.check_subscription(user_id)

        if is_member:

            try:

                # ✅ پاسخ اولیه به Callback Query
                self.bot.answer_callback_query(call.id, t(call.message, "checking_membership"), show_alert=False)
                self.bot.edit_message_text(t(call.message, "membership_confirmed"),
                                           chat_id=chat_id, message_id=call.message.message_id)

                from telbot.views import start
                start(call.message)
            except Exception as e:
                self.bot.send_message(user_id, f"error iis: {e}")
        else:
            self.bot.answer_callback_query(call.id, t(call.message, "not_subscribed"), show_alert=True)

    def register_handlers(self):
        """🔹 ثبت هندلرهای مورد نیاز"""
        self.bot.callback_query_handler(func=lambda call: call.data == "check_subscription2")(self.handle_check_subscription)

    def check_subscription(self, user, channels=None):
        """✅ بررسی می‌کند که کاربر در کانال عضو شده است یا نه"""
        if channels is None:
            channels = self.my_channels_with_atsign
        for channel in channels:
            try:
                is_member = self.bot.get_chat_member(chat_id=channel, user_id=user)
                if is_member.status in ["kicked", "left"]:
                    return False
            except Exception as e:
                
                logger.error(f"🚨 خطا در بررسی عضویت کاربر {user} در کانال {channel}: {e}")
                return False
        return True

    def subscription_offer(self, message):
        """❌ اگر کاربر عضو نباشد، دکمه‌های عضویت نمایش داده شوند"""
        channel_markup = types.InlineKeyboardMarkup()
        check_subscription_button = types.InlineKeyboardButton(text=t(message, "subscribed"), callback_data='check_subscription2')
        channel_subscription_button = types.InlineKeyboardButton(text=t(message, "join_channel"), url=f"https://t.me/{self.my_channels_without_atsign[0]}")
        group_subscription_button = types.InlineKeyboardButton(text=t(message, 'join_group'), url=f"https://t.me/{self.my_channels_without_atsign[1]}")

        channel_markup.add(channel_subscription_button, group_subscription_button)
        channel_markup.add(check_subscription_button)

        if not self.check_subscription(user=message.from_user.id):
            self.bot.send_message(message.chat.id, t(message, "verify_membership"), reply_markup=channel_markup)
            return False
        return True

subscription = SubscriptionClass(app)

############################  SEND MENU  ############################

# Helper function to send menu
def send_menu(message, options, current_menu, extra_buttons=None, cols=3, extra_cols=2):
    """Send a translated menu with options and update the session."""

    if subscription.subscription_offer(message):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        # زبان کاربر
        profile = ProfileModel.objects.get(tel_id=message.chat.id)
        lang = profile.lang if profile.lang else "fa"

        # ترجمه گزینه‌های اصلی
        rows = [options[i:i + cols] for i in range(0, len(options), cols)]
        for row in rows:
            translated_row = [
                translations.get(key, {}).get(lang, translations.get(key, {}).get("en", key))
                for key in row
            ]
            markup.row(*translated_row)

        # ترجمه گزینه‌های اضافه
        if extra_buttons:
            extra_rows = [extra_buttons[i:i + extra_cols] for i in range(0, len(extra_buttons), extra_cols)]
            for extra_row in extra_rows:
                translated_row = [
                    translations.get(key, {}).get(lang, translations.get(key, {}).get("en", key))
                    for key in extra_row
                ]
                markup.row(*translated_row)

        return markup


############################  SEE PRODUCTS  ############################

# Top discounts
def handle_products(message):
    if subscription.subscription_offer(message):
        chat_id = message.chat.id
        subcategory = message.text
        options = [t(message, "most_selling"), t(message, "most_expensive"), t(message, "cheapest"), t(message, "most_discounted")]

        markup = send_menu(message, options, "products", retun_menue)
        session = session_manager.get_user_session(chat_id, namespace="menu")
        current_category = Category.objects.get(title__iexact=session["current_menu"], status=True)
        app.send_message(chat_id, f"{current_category.get_full_path()}", reply_markup=markup)


############################  CATEGORY MENU  ############################

class CategoryClass:

    def __init__(self):
        pass

    def handle_category(self, message):
        if subscription.subscription_offer(message):
            try:
                session = session_manager.get_user_session(message.chat.id, namespace="menu")
                print(f"begining of handle_category: {session}")
                profile = ProfileModel.objects.get(tel_id=message.chat.id)
                if profile.seller_mode:
                    store = Store.objects.get(owner=profile)
                else:
                    store = profile.server_store
                if not session.get("category") and not session.get("product") and not store.categories.exists():
                    # Store has no categories
                    app.send_message(message.chat.id, t(message, "store_empty"))
                    return
                    
                    # do something...
                if session.get("category") and session.get("menu_delete") and session.get("delete_sure"):
                    text = t(message, "category_deleted_successfully")
                    session["delete_sure"] = False
                    session_manager.set_user_session(message.chat.id, session, namespace="menu")
                elif session.get("category") and session.get("menu_delete"):
                    if not store.categories.exists():
                        app.send_message(message.chat.id, t(message, "no_category_to_delete"))
                        session["menu_delete"] = False
                        session_manager.set_user_session(message.chat.id, session, namespace="menu")
                        return
                    text = t(message, "delete_category_title_prompt") + "\n\n" + t(message, "delete_category_warning")
                elif session.get("category") and session.get("menu_add"):
                    if not store.categories.exists():
                        self.add_category(message)
                        return
                    text = t(message, "add_subcategory_select_parent")
                elif session.get("category") and session.get("category_deactivate"):
                    text = t(message, "choose_category_toggle")
                elif session.get("product"):
                    text = t(message, "select_subcategory_for_product")
                elif not session.get("category") and not session.get("product"):
                    button = [t(message, "delete_category_and_subcategories"), ]
                    for b in button:
                        home_menu.remove(b) if b in home_menu else None
                    text = t(message, "product_category_question")
                else:
                    text = t(message, "category_deleted_successfully")
                cats = Category.objects.filter(parent__isnull=True, status=True, store=store).values_list('title', flat=True)
                markup = send_menu(message, cats, message.text, home_menu, extra_cols=1)
                app.send_message(message.chat.id, text, reply_markup=markup)
            except Exception as e:
                app.send_message(message.chat.id, "خطایی رخ داده است. لطفاً دوباره تلاش کنید.")
                print(f"Error: {traceback.format_exc()}")

    def handle_subcategory(self, message):
        try:
            if subscription.subscription_offer(message):
                current_category = Category.objects.get(title__iexact=message.text.title(), status=True)
                children = [child.title for child in current_category.get_next_layer_categories()]

                session = session_manager.get_user_session(message.chat.id, namespace="menu")
                session["current_menu"] = message.text.lower()
                session_manager.set_user_session(message.chat.id, session, namespace="menu")
                print(f"begining of handle_subcategory: {session}")

                if children == []:
                    if session.get("category") and session.get("menu_delete"):
                        self.delete_sure(message)
                        try:
                            message.text = current_category.get_parents()[0].title
                        except:
                            pass
                    elif session.get("category") and session.get("menu_add"):
                        self.add_category(message)
                        try:
                            print(current_category)
                            print(current_category.get_parents())
                            message.text = current_category.get_parents()[0].title
                        except:
                            pass
                    elif session.get("category") and session.get("category_deactivate"):
                        self.deactivate_category_sure(message)
                        # message.text = current_category.get_parents()[0].title
                    else:
                        if session.get('product_cat_selection'):
                            a = ProductBot(app)
                            a.get_category(message)
                        else:
                            fake_message = message
                            fake_message.text = "hi"
                            handle_products(fake_message)
                else:
                    if session.get("category"):
                        if session.get("menu_delete"):
                            button = t(message, "delete_category_and_subcategories")
                            retun_menue.append(button) if button not in retun_menue else retun_menue
                        elif session.get("category_deactivate"):
                            button = t(message, "deactivate_category")
                            retun_menue.append(button) if button not in retun_menue else retun_menue
                    markup = send_menu(message, children, message.text, retun_menue)
                    if session.get("category") and session.get("menu_delete") and session.get("delete_sure"):
                        text = t(message, "category_deleted_successfully")
                        session["delete_sure"] = False
                        session_manager.set_user_session(message.chat.id, session, namespace="menu")
                    else:
                        button = [t(message, "delete_category_and_subcategories"), t(message, "deactivate_category")]
                        for b in button:
                            retun_menue.remove(b) if b in retun_menue else None
                        text = f"{Category.objects.get(title__iexact=session['current_menu'], status=True).get_full_path()}"
                    app.send_message(message.chat.id, text, reply_markup=markup)
        except Exception as e:
            print(f"Error: {traceback.format_exc()}")

    def add_category(self, message):
        try:
            session = session_manager.get_user_session(message.chat.id, namespace="menu")

            # Mark we are waiting for new category title
            session["get_new_category"] = True

            # IMPORTANT: Only set current_menu if we are actually inside a category
            if session.get("current_menu"):
                # user is inside a category, so add to that category
                session["parent_for_new"] = session["current_menu"]
            else:
                # user is in root menu
                session["parent_for_new"] = None  

            button = [t(message, "delete_category_and_subcategories"), t(message, "deactivate_category")]
            for b in button:
                if b in home_menu:
                    home_menu.remove(b)

            markup = send_menu(message, [t(message, "cancel_action")], 'cat_delete_sure', home_menu)
            session_manager.set_user_session(message.chat.id, session, namespace="menu")

            app.send_message(message.chat.id, t(message, "enter_new_category_title"), reply_markup=markup)

        except Exception as e:
            print(traceback.format_exc())


    def deactivate_category_sure(self, message):
        session = session_manager.get_user_session(message.chat.id, namespace="menu")
        session["deactivate_category_sure"] = True
        markup = send_menu(message, [t(message, "yes_im_sure"), t(message, "cancel_action")], 'cat_delete_sure', home_menu)
        session_manager.set_user_session(message.chat.id, session, namespace="menu")
        app.send_message(message.chat.id, t(message, "confirm_deactivate_category"), reply_markup=markup)

    def delete_sure(self, message):
        try:
            session = session_manager.get_user_session(message.chat.id, namespace="menu")
            session["delete_sure"] = True
            markup = send_menu(message, [t(message, "yes_im_sure"), t(message, "cancel_action")], 'cat_delete_sure', home_menu)
            session_manager.set_user_session(message.chat.id, session, namespace="menu")
            app.send_message(message.chat.id, t(message, "confirm_delete_category"), reply_markup=markup)
        except Exception as e:
            print(traceback.format_exc())
        

############################  ADD PRODUCT  ############################

# ایجاد slug یکتا
def generate_unique_slug(model, name):
    from django.utils.text import slugify

    slug = slugify(name)
    unique_slug = slug
    counter = 1
    while model.objects.filter(slug=unique_slug).exists():
        unique_slug = f"{slug}-{counter}"
        counter += 1
    return unique_slug



def download_and_save_image(file_id, bot):
    try:
        # دانلود فایل
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        # مسیر ذخیره‌سازی
        save_dir = os.path.join(sett.MEDIA_ROOT, "product_images")
        os.makedirs(save_dir, exist_ok=True)  # ایجاد مسیر در صورت عدم وجود

        file_path = os.path.join(save_dir, file_info.file_path.split('/')[-1])

        # ذخیره فایل در سیستم
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        return file_path  # مسیر ذخیره‌شده را برمی‌گرداند
    except Exception as e:
        print(f"خطا در ذخیره تصویر: {e}")
        return None



class ProductBot:
    def __init__(self, bot: TeleBot):
        self.bot = bot

    class ProductState:
        NAME = "name"
        SLUG = "slug"
        BRAND = "brand"
        PRICE = "price"
        DISCOUNT = "discount"
        STOCK = "stock"
        STATUS = "status"
        CATEGORY = "category"
        VARIANT_DECIDE = "variant_decide"
        VARIANT_KEY = "variant_key"
        VARIANT_VALUES = "variant_values"
        VARIANT_ADD_ANOTHER_KEY = "variant_add_key"
        VARIANT_CONFIRM_COMBINATIONS = "variant_confirm_combinations"
        VARIANT_STOCKS = "variant_stocks"
        DESCRIPTION = "description"
        CODE = "code"
        MAIN_IMAGE = "main_image"
        ADDITIONAL_IMAGES = "additional_images"
        ATTRIBUTES = "attributes"
        DELETE = "delete"
        DELETE_CONFIRM = "delete_confirm"
        DEACTIVATE = "deactivate"
        DEACTIVATE_CONFIRM = "deactivate_confirm"




    def register_handlers(self):
        """Register message handlers."""
        self.bot.register_message_handler(self.cancle_request, func=lambda message: message.text == t(message, "cancel_action"))
        self.bot.register_message_handler(self.get_name, func=self.is_state(self.ProductState.NAME))
        self.bot.register_message_handler(self.get_brand, func=self.is_state(self.ProductState.BRAND))
        self.bot.register_message_handler(self.get_price, func=self.is_state(self.ProductState.PRICE))
        self.bot.register_message_handler(self.get_discount, func=self.is_state(self.ProductState.DISCOUNT))
        self.bot.register_message_handler(self.get_stock, func=self.is_state(self.ProductState.STOCK))
        self.bot.register_message_handler(self.get_status, func=self.is_state(self.ProductState.STATUS))
        self.bot.register_message_handler(self.get_category, func=self.is_state(self.ProductState.CATEGORY))

        # Variant workflow
        self.bot.register_message_handler(self.get_variant_decision, func=self.is_state(self.ProductState.VARIANT_DECIDE))
        self.bot.register_message_handler(self.get_variant_key, func=self.is_state(self.ProductState.VARIANT_KEY))
        self.bot.register_message_handler(self.get_variant_values, func=self.is_state(self.ProductState.VARIANT_VALUES))
        self.bot.register_message_handler(self.get_variant_add_key_answer, func=self.is_state(self.ProductState.VARIANT_ADD_ANOTHER_KEY))
        self.bot.register_message_handler(self.get_variants_stock_values, func=self.is_state(self.ProductState.VARIANT_STOCKS))


        self.bot.register_message_handler(self.get_description, func=self.is_state(self.ProductState.DESCRIPTION))
        self.bot.register_message_handler(self.get_product_attributes, func=self.is_state(self.ProductState.ATTRIBUTES))
        self.bot.register_message_handler(self.get_main_image, func=self.is_state(self.ProductState.MAIN_IMAGE), content_types=["photo"])
        self.bot.register_message_handler(self.get_additional_images, func=self.is_state(self.ProductState.ADDITIONAL_IMAGES), content_types=["photo"])
        self.bot.register_message_handler(self.delete, func=self.is_state(self.ProductState.DELETE))
        self.bot.register_message_handler(self.delete_confirm, func=self.is_state(self.ProductState.DELETE_CONFIRM))
        self.bot.register_message_handler(self.deactivate, func=self.is_state(self.ProductState.DEACTIVATE))
        self.bot.register_message_handler(self.deactivate_confirm, func=self.is_state(self.ProductState.DEACTIVATE_CONFIRM))
        


    def is_state(self, state):
        def check(message: Message):
            state_manager = RedisStateManager(message.chat.id)
            return state_manager.get_state() == state
        return check


    def set_state(self, chat_id, state):
        RedisStateManager(chat_id).set_state(state)


    def save_user_data(self, chat_id, key, value):
        RedisStateManager(chat_id).save_user_data(key, value)


    def get_user_data(self, chat_id, key, default=None):
        value = RedisStateManager(chat_id).get_user_data(key)
        return value if value is not None else default

    def reset_state(self, chat_id):
        RedisStateManager(chat_id).delete_state()


    def get_name(self, message: Message):
        # ذخیره نام در Redis
        self.save_user_data(message.chat.id, "name", message.text)
        self.set_state(message.chat.id, self.ProductState.BRAND)

        # ارسال منو برای وارد کردن برند
        markup = send_menu(message, [t(message, "no_brand")], message.text, [t(message, "cancel_action")])
        self.bot.send_message(message.chat.id, t(message, "enter_product_brand"), reply_markup=markup)


    def get_brand(self, message: Message):
        # ذخیره برند در Redis
        brand = None if message.text == t(message, "no_brand") else message.text
        self.save_user_data(message.chat.id, "brand", brand)
        self.set_state(message.chat.id, self.ProductState.PRICE)

        # ارسال منو برای وارد کردن قیمت
        markup = send_menu(message, [t(message, "cancel_action")], message.text)
        self.bot.send_message(message.chat.id, t(message, "enter_product_price"), reply_markup=markup)



    def get_price(self, message: Message):
        try:
            # تلاش برای تبدیل پیام به عدد
            price = float(message.text)

            # بررسی اینکه قیمت معتبر است یا خیر
            if price < 10000:
                self.bot.send_message(
                    message.chat.id, t(message, "final_price_too_low"))
                return  # خروج از تابع تا کاربر دوباره قیمت وارد کند

            # ذخیره قیمت در Redis
            self.save_user_data(message.chat.id, "price", price)
            self.set_state(message.chat.id, self.ProductState.DISCOUNT)

            # ارسال پیام برای درخواست درصد تخفیف
            self.bot.send_message(message.chat.id, t(message, "enter_discount"))
        except ValueError:
            # مدیریت خطای تبدیل مقدار نامعتبر
            self.bot.send_message(message.chat.id, t(message, "price_not_number"))



    def get_discount(self, message: Message):
        try:
            # تلاش برای تبدیل تخفیف به عدد
            discount = float(message.text)

            # دریافت قیمت و محاسبه قیمت نهایی از Redis
            price = self.get_user_data(message.chat.id, "price") or 0  # اگر قیمت وجود نداشت، مقدار پیش‌فرض 0 استفاده می‌شود
            final_price = price - ((price * discount) / 100)

            # بررسی اینکه قیمت نهایی معتبر است یا خیر
            if final_price < 10000:
                self.bot.send_message(
                    message.chat.id, t(message, "final_price_too_low"))
                self.set_state(message.chat.id, self.ProductState.PRICE)  # بازگشت به مرحله قیمت
                return

            # ذخیره تخفیف در Redis و ادامه به مرحله بعد
            self.save_user_data(message.chat.id, "discount", discount)
            self.set_state(message.chat.id, self.ProductState.STOCK)

            # ارسال پیام برای دریافت توضیحات
            self.bot.send_message(message.chat.id, t(message, "enter_stock"))
        except ValueError:
            # مدیریت خطای تبدیل مقدار نامعتبر
            self.bot.send_message(
                message.chat.id,
                t(message, "discount_not_number")
            )




    def get_stock(self, message: Message):
        try:
            stock = int(message.text)

            # ذخیره موجودی در Redis
            self.save_user_data(message.chat.id, "stock", stock)
            self.set_state(message.chat.id, self.ProductState.STATUS)
            markup = send_menu(message, [t(message, "active_adj"), t(message, "inactive_adj")], message.text, [t(message, "cancel_action")])
            app.send_message(message.chat.id, t(message, "enter_status"), reply_markup=markup)

        except ValueError:
            self.bot.send_message(message.chat.id, t(message, "balance_not_integer"))



    def get_status(self, message: Message):
        try:
            status = message.text.strip() == t(message, "active_adj")

            # ذخیره وضعیت موجود بودن کالا در Redis
            self.save_user_data(message.chat.id, "status", status)
            self.set_state(message.chat.id, self.ProductState.CATEGORY)
            session = session_manager.get_user_session(message.chat.id, namespace="menu")
            session['product_cat_selection'] = True
            session['add_product'] = True
            # نمایش منوی دسته‌بندی اصلی
            cat = CategoryClass()
            cat.handle_category(message)
            session['add_product'] = False
            session_manager.set_user_session(message.chat.id, session, namespace="menu")


        except Exception as e:
            self.bot.send_message(message.chat.id, "خطایی رخ داده است. لطفاً دوباره تلاش کنید.")
            print(f"Error: {e}")



    def get_category(self, message: Message):
        try:
            selected_category = Category.objects.get(title__iexact=message.text.strip(), status=True)
            self.save_user_data(message.chat.id, "category_id", selected_category.id)
            self.set_state(message.chat.id, self.ProductState.VARIANT_DECIDE)
            markup = send_menu(message, [t(message, "accurate_inventory"), t(message, "not_necessary")], "main menu", [t(message, "cancel_action")])
            self.bot.send_message(message.chat.id, t(message, "ask_variant_decision"), reply_markup=markup)
        except Category.DoesNotExist:
            self.bot.send_message(message.chat.id, t(message, "invalid_selected_category"))


    # ----------------------------
    # Variant workflow handlers
    # ----------------------------
    def get_variant_decision(self, message: Message):
        try:
            if message.text == t(message, "accurate_inventory"):
                self.save_user_data(message.chat.id, "variants", {})
                self.set_state(message.chat.id, self.ProductState.VARIANT_KEY)
                markup = send_menu(message, [t(message, "cancel_action")], message.text)
                self.bot.send_message(message.chat.id, t(message, "enter_variant_key"), reply_markup=markup)
            else:
                # Skip variants, go to images
                self.set_state(message.chat.id, self.ProductState.DESCRIPTION)
                markup = send_menu(message, [t(message, "no_description")], "main menu", [t(message, "cancel_action")])
                self.bot.send_message(message.chat.id, t(message, "enter_description"), reply_markup=markup)
        except Exception as e:
            print(traceback.format_exc())

    def get_variant_key(self, message: Message):
        try:
            key = message.text.strip()
            variants = self.get_user_data(message.chat.id, "variants")
            if key in variants:
                self.bot.send_message(message.chat.id, t(message, "variant_key_exists"))
                return
            variants[key] = []
            self.save_user_data(message.chat.id, "current_variant_key", key)
            self.save_user_data(message.chat.id, "variants", variants)
            self.set_state(message.chat.id, self.ProductState.VARIANT_VALUES)
            self.bot.send_message(message.chat.id, t(message, "enter_variant_values", keyname=key))
        except Exception as e:
            print(traceback.format_exc())

    def get_variant_values(self, message: Message):
        try:
            # تبدیل همه ویرگول‌ها به کامای انگلیسی
            normalized_text = (
                message.text
                .replace("،", ",")   # فارسی و عربی
                .replace("，", ",")   # چینی
                .replace("﹐", ",")   # کامای عربی-قدیمی
                .replace("､", ",")   # کامای ژاپنی
            )

            # جدا کردن مقادیر
            values = [v.strip() for v in normalized_text.split(",") if v.strip()]

            key = self.get_user_data(message.chat.id, "current_variant_key")
            variants = self.get_user_data(message.chat.id, "variants")
            variants[key] = values
            self.save_user_data(message.chat.id, "variants", variants)

            # رفتن به مرحله‌ی بعد
            self.set_state(message.chat.id, self.ProductState.VARIANT_ADD_ANOTHER_KEY)
            markup = send_menu(
                message,
                [t(message, "yes"), t(message, "no")],
                "main menu",
                [t(message, "cancel_action")]
            )
            self.bot.send_message(
                message.chat.id,
                t(message, "add_another_variant_key"),
                reply_markup=markup
            )

        except Exception as e:
            print(traceback.format_exc())

    def get_variant_add_key_answer(self, message: Message):
        try:
            chat_id = message.chat.id
            text = message.text.strip()

            if text == t(message, "yes"):
                self.set_state(chat_id, self.ProductState.VARIANT_KEY)
                markup = send_menu(message, [t(message, "cancel_action")], message.text)
                self.bot.send_message(chat_id, t(message, "enter_next_variant_key"), reply_markup=markup)
                return

            # یعنی گفته "خیر" → همه‌ی کلیدها جمع شدند
            variants = self.get_user_data(chat_id, "variants")
            keys = list(variants.keys())
            values = list(variants.values())

            # تمام ترکیب‌ها از همه مقدارها ساخته می‌شوند
            combinations = list(itertools.product(*values))
            self.save_user_data(chat_id, "variant_combinations", combinations)
            self.save_user_data(chat_id, "variant_stock_index", 0)
            self.save_user_data(chat_id, "variants_stock", [])

            # پیام مقدمه
            readable_keys = "، ".join(keys)
            markup = send_menu(message, [t(message, "cancel_action")], message.text)
            self.bot.send_message(
                chat_id,
                t(message, "variant_stock_intro", keys=readable_keys),
                reply_markup=markup
            )

            # ترکیب اول را آماده کنیم
            first_combo = combinations[0]
            combo_text = " ".join([f"{keys[i]}: {first_combo[i]}" for i in range(len(keys))])

            self.set_state(chat_id, self.ProductState.VARIANT_STOCKS)
            self.bot.send_message(chat_id, t(message, "enter_variant_stock", combo=combo_text))
        except Exception as e:
            print(traceback.format_exc())

    def get_variants_stock_values(self, message: Message):
        chat_id = message.chat.id
        stock_str = message.text.strip()

        # --- اعتبارسنجی اولیه
        if not stock_str.isdigit():
            self.bot.send_message(chat_id, t(message, "invalid_stock_input"))
            return

        stock = int(stock_str)

        # --- بازیابی داده‌ها
        total_stock = self.get_user_data(chat_id, "stock")  # موجودی کلی محصول
        combinations = self.get_user_data(chat_id, "variant_combinations")
        index = self.get_user_data(chat_id, "variant_stock_index", 0)
        variants_stock = self.get_user_data(chat_id, "variants_stock", [])

        # --- محاسبه مجموع فعلی
        current_total = sum(item["stock"] for item in variants_stock)

        # بررسی اینکه واردکردن این عدد باعث تجاوز از موجودی کل نشود
        if current_total + stock > total_stock:
            remaining = total_stock - current_total
            self.bot.send_message(
                chat_id,
                t(message, "stock_exceed_total", total=total_stock, current=current_total, remaining=remaining)
            )
            return  # در همین state باقی بماند

        # --- ذخیره موجودی ترکیب فعلی
        variants_stock.append({
            "combination": combinations[index],
            "stock": stock
        })
        self.save_user_data(chat_id, "variants_stock", variants_stock)

        # --- برو سراغ بعدی یا پایان کار
        current_total += stock

        if current_total >= total_stock:
            # ✅ جمع دقیقاً برابر با موجودی کل شد
            total = sum(item["stock"] for item in variants_stock)
            text = t(message, "variant_stock_saved", total=total)
            self.set_state(message.chat.id, self.ProductState.DESCRIPTION)
            markup = send_menu(
                message,
                [t(message, "no_description")],
                "main menu",
                [t(message, "cancel_action")]
            )
            self.bot.send_message(chat_id, text, reply_markup=markup)
            return

        # اگر هنوز ترکیب‌هایی مانده بود و مجموع کمتر از کل است
        index += 1
        if index < len(combinations):
            self.save_user_data(chat_id, "variant_stock_index", index)
            variants = self.get_user_data(chat_id, "variants")
            keys = list(variants.keys())
            combo_text = " ".join([f"{keys[i]}: {combinations[index][i]}" for i in range(len(keys))])
            remaining = total_stock - current_total
            self.bot.send_message(
                chat_id,
                t(message, "variant_stock_question", combo_text=combo_text, remaining=remaining)
            )
        else:
            # اگر همه ترکیب‌ها تمام شدند ولی هنوز موجودی کل پر نشده
            total = sum(item["stock"] for item in variants_stock)
            self.bot.send_message(
                chat_id,
                t(message, "stock_less_than_total", total=total, total_stock=total_stock)
            )
            text = t(message, "variant_stock_partial_saved", total=total) + t(message, "enter_description")
            self.set_state(message.chat.id, self.ProductState.DESCRIPTION)
            markup = send_menu(
                message,
                [t(message, "no_description")],
                "main menu",
                [t(message, "cancel_action")]
            )
            self.bot.send_message(chat_id, text, reply_markup=markup)


    def get_description(self, message: Message):
        # ذخیره خصوصیات محصول در Redis
        description = None if message.text == t(message, "no_description") else message.text
        self.save_user_data(message.chat.id, "description", description)

        # تغییر وضعیت به مرحله ویژگی‌ها
        self.set_state(message.chat.id, self.ProductState.ATTRIBUTES)

        # ایجاد دکمه پایان
        markup = types.InlineKeyboardMarkup()
        finish_button = types.InlineKeyboardButton(text=t(message, "no_ads_features"), callback_data="finish_attributes")
        markup.add(finish_button)

        # ارسال پیام برای درخواست ویژگی‌های تبلیغاتی
        self.bot.send_message(
            message.chat.id,
            t(message, "enter_ads_features"),
            reply_markup=markup
        )

        # ارسال منو اصلی
        markup = send_menu(message, [], "main menu", [t(message, "cancel_action")])
        self.bot.edit_message_reply_markup(
            chat_id=message.chat.id,
            message_id=message.message_id,
            reply_markup=markup
        )




    def get_product_attributes(self, message: Message):
        # نمایش پیام برای وارد کردن ویژگی‌های محصول
        markup = types.InlineKeyboardMarkup()
        finish_button = types.InlineKeyboardButton(text=t(message, "finish"), callback_data="finish_attributes")
        markup.add(finish_button)

        key = message.text.split(":")[0]  # کلید ویژگی (مانند "وزن")
        if ":" not in message.text:
            value = ""
        else:
            value = message.text.split(":")[1]  # مقدار ویژگی (مانند "1kg")

        # بازیابی ویژگی‌ها از Redis
        state_manager = RedisStateManager(message.chat.id)
        product_attributes = state_manager.get_user_data("product_attributes") or {}
        product_attributes[key] = value

        # ذخیره ویژگی‌های جدید در Redis
        state_manager.save_user_data("product_attributes", product_attributes)

        self.bot.send_message(
            message.chat.id,
            t(message, "enter_ads_features"),
            reply_markup=markup
        )
        self.set_state(message.chat.id, self.ProductState.ATTRIBUTES)  # وضعیت به حالت ویژگی‌های محصول تغییر می‌کن

    def handle_finish_attributes(self, callback_query: types.CallbackQuery):
        try:
            chat_id = callback_query.message.chat.id

            # تغییر وضعیت به تصویر اصلی
            self.set_state(chat_id, self.ProductState.MAIN_IMAGE)
            self.bot.send_message(chat_id, t(callback_query.message, "send_main_image"))
        except Exception as e:
            self.bot.send_message(callback_query.message.chat.id, "خطا در ذخیره ویژگی رخ داده است.")
            print(f"Error: {e}")

    def register_handle_finish_attributes(self):
        self.bot.callback_query_handler(func=lambda call: call.data == 'finish_attributes')(self.handle_finish_attributes)



    def get_main_image(self, message: Message):
        try:
            # دانلود و ذخیره تصویر
            file_id = message.photo[-1].file_id
            saved_path = download_and_save_image(file_id, self.bot)

            if saved_path:
                # ذخیره مسیر تصویر در Redis
                state_manager = RedisStateManager(message.chat.id)
                state_manager.save_user_data("main_image", saved_path)  # ذخیره مسیر تصویر در Redis

                # تغییر وضعیت به مرحله بعدی (تصاویر اضافی)
                self.set_state(message.chat.id, self.ProductState.ADDITIONAL_IMAGES)
                self.bot.send_message(message.chat.id, t(message, "send_three_more_images"))
            else:
                self.bot.send_message(message.chat.id, "خطا در ذخیره تصویر اصلی رخ داده است.")
        except Exception as e:
            self.bot.send_message(message.chat.id, "خطایی رخ داده است. لطفاً دوباره تلاش کنید.")
            print(f"Error: {e}")


    def generate_readable_sku(self, product_name, combo_list, product_id, attempt=1):
        """
        Generate a readable, unique SKU for each product variant
        Example output: SHIRT-BLUE-L-001
        """
        base_name = re.sub(r'[^A-Z0-9]', '', product_name.upper().replace(" ", ""))[:6]
        variant_part = "-".join(str(v).upper().replace(" ", "")[:4] for v in combo_list)
        sku = f"{base_name}-{variant_part}-{attempt:03d}"

        if ProductVariant.objects.filter(sku=sku).exists():
            return self.generate_readable_sku(product_name, combo_list, product_id, attempt + 1)
        return sku


    def get_additional_images(self, message: Message):
        try:
            chat_id = message.chat.id

            # Save the additional image
            additional_images = self.get_user_data(chat_id, "additional_images") or []
            file_id = message.photo[-1].file_id
            saved_image = download_and_save_image(file_id, self.bot)

            if not saved_image:
                self.bot.send_message(chat_id, t(message, "extra_image_save_failed"))
                return

            additional_images.append(saved_image)
            self.save_user_data(chat_id, "additional_images", additional_images)

            if len(additional_images) < 3:
                remaining = 3 - len(additional_images)
                self.bot.send_message(chat_id, t(message, "send_extra_images", pic_num=remaining))
                return

            # Retrieve user, store, and category
            profile = ProfileModel.objects.get(tel_id=message.from_user.id)
            store = Store.objects.get(owner=profile)

            category_id = self.get_user_data(chat_id, "category_id")
            if not category_id:
                self.bot.send_message(chat_id, t(message, "invalid_selected_category"))
                return
            category = Category.objects.get(id=category_id, status=True)

            # Product basic info
            name = self.get_user_data(chat_id, "name")
            slug = generate_unique_slug(Product, name)
            price = self.get_user_data(chat_id, "price") or 10000
            discount = self.get_user_data(chat_id, "discount") or 0
            stock = self.get_user_data(chat_id, "stock") or 0
            status = self.get_user_data(chat_id, "status") or True

            product = Product.objects.create(
                profile=profile,
                store=store,
                name=name,
                brand=self.get_user_data(chat_id, "brand"),
                price=price,
                discount=discount,
                stock=stock,
                status=status,
                category=category,
                description=self.get_user_data(chat_id, "description"),
                main_image=self.get_user_data(chat_id, "main_image"),
                slug=slug
            )

            # Product attributes
            product_attrs = self.get_user_data(chat_id, "product_attributes") or {}
            for key, value in product_attrs.items():
                ProductAttribute.objects.create(product=product, key=key, value=value)

            # Variants
            variants = self.get_user_data(chat_id, "variants") or {}
            variant_combinations = self.get_user_data(chat_id, "variant_combinations") or []
            variants_stock = self.get_user_data(chat_id, "variants_stock") or []
            entries = variants_stock or [{"combination": combo, "stock": 0} for combo in variant_combinations]

            option_cache = {}
            value_cache = {}
            keys_order = list(variants.keys())

            if entries:
                for entry in entries:
                    combo_raw = entry.get("combination") or entry.get("combo")
                    stock = int(entry.get("stock", 0)) if entry.get("stock") else 0
                    combo_list = list(combo_raw.values()) if isinstance(combo_raw, dict) else list(combo_raw)

                    if len(combo_list) != len(keys_order):
                        print(f"[warn] combo length mismatch: keys={keys_order} combo={combo_list}")
                        continue

                    sku = self.generate_readable_sku(product.name, combo_list, product.id)
                    variant = ProductVariant.objects.create(product=product, stock=stock, sku=sku)

                    for i, key_name in enumerate(keys_order):
                        val = combo_list[i]

                        if key_name not in option_cache:
                            option_obj, _ = ProductOption.objects.get_or_create(product=product, name=key_name)
                            option_cache[key_name] = option_obj
                        else:
                            option_obj = option_cache[key_name]

                        if (key_name, val) not in value_cache:
                            value_obj, _ = ProductOptionValue.objects.get_or_create(option=option_obj, value=val)
                            value_cache[(key_name, val)] = value_obj
                        else:
                            value_obj = value_cache[(key_name, val)]

                        variant.values.add(value_obj)
            else:
                # If product has no variants, generate a simple SKU
                ProductVariant.objects.create(
                    product=product,
                    stock=stock,
                    sku=f"{re.sub(r'[^A-Z0-9]', '', product.name.upper())[:8]}-{product.id:03d}"
                )

            # Save extra images
            for image_path in additional_images:
                ProductImage.objects.create(product=product, image=image_path)

            # Send success message
            markup = send_menu(message, profile.tel_menu, "main menu", profile.extra_button_menu)
            self.bot.send_message(chat_id, t(message, "product_saved"), reply_markup=markup)
            self.reset_state(chat_id)

        except Exception as e:
            print(f"Error in get_additional_images: {e}\n{traceback.format_exc()}")
            self.bot.send_message(message.chat.id, t(message, "product_save_failed"))



    def delete(self, message: Message):
        try:
            if message.text == t(message, "cancel_action"):
                self.cancle_request(message)
            else:
                code = message.text
                try:
                    product = Product.objects.get(code=code)
                    attributes = product.attributes.all()
                    # ارسال پیام محصول به کاربر
                    producthandler = ProductHandler(app=self.bot, product=product, current_site='https://intelleum.ir:8443', attributes=attributes)
                    producthandler.send_product_message(chat_id=message.chat.id, buttons=False)

                    # ذخیره اطلاعات محصول در Redis
                    state_manager = RedisStateManager(message.chat.id)
                    state_manager.save_user_data("product_code", code)

                    menu = [t(message, "yes_im_sure"), t(message, "cancel_action")]
                    markup = send_menu(message, menu, "main menu", home_menu)
                    self.bot.send_message(message.chat.id, t(message, "confirm_delete_product"), reply_markup=markup)
                    self.set_state(message.chat.id, self.ProductState.DELETE_CONFIRM)
                    self.bot.register_next_step_handler(message, self.delete_confirm)

                except Product.DoesNotExist:
                    self.bot.send_message(message.chat.id, t(message, "product_code_not_found"))
                    return
        except Exception as e:
            error_message = traceback.format_exc()  # دریافت Traceback کامل
            print(f"Error in handle_buttons: {e}\n{error_message}")




    def delete_confirm(self, message):
        try:
            print("hi")
            state_manager = RedisStateManager(message.chat.id)

            # بازیابی کد محصول از Redis
            product_code = state_manager.get_user_data("product_code")
            if product_code:
                try:
                    product = Product.objects.get(code=product_code)
                    if message.text == t(message, "yes_im_sure"):
                        # حذف محصول از دیتابیس
                        product.delete()
                        print("yes")

                        # ارسال پیام موفقیت‌آمیز به کاربر
                        main_menu = ProfileModel.objects.get(tel_id=message.from_user.id).tel_menu
                        extra_button_menu = ProfileModel.objects.get(tel_id=message.from_user.id).extra_button_menu
                        markup = send_menu(message, main_menu, "main menu", extra_button_menu)
                        self.bot.send_message(message.chat.id, t(message, "product_deleted"), reply_markup=markup)

                    elif message.text == t(message, "cancel_action"):
                        self.cancle_request(message)
                        return

                    self.reset_state(message.chat.id)
                except Product.DoesNotExist:
                    self.bot.send_message(message.chat.id, t(message, "product_code_not_found"))
                    return
            else:
                self.bot.send_message(message.chat.id, "کد محصول ذخیره نشده است.")
                return

        except Exception as e:
            self.bot.send_message(message.chat.id, "خطایی رخ داده است. لطفاً دوباره تلاش کنید.")
            print(f"Error: {e}")

    def deactivate(self, message):
        try:
            if message.text == t(message, "cancel_action"):
                self.cancle_request(message)
            else:
                code = message.text
                try:
                    product = Product.objects.get(code=code)
                    attributes = product.attributes.all()
                    # ارسال پیام محصول به کاربر
                    producthandler = ProductHandler(app=self.bot, product=product, current_site='https://intelleum.ir:8443', attributes=attributes)
                    producthandler.send_product_message(chat_id=message.chat.id, buttons=False)

                    # ذخیره اطلاعات محصول در Redis
                    state_manager = RedisStateManager(message.chat.id)
                    state_manager.save_user_data("product_code", code)

                    menu = [t(message, "yes_im_sure"), t(message, "cancel_action")]
                    markup = send_menu(message, menu, "main menu", home_menu)
                    action_text = t(message, "deactivate") if product.status else t(message, "activate")
                    msg_text = t(message, "confirm_toggle_product", action=action_text)
                    self.bot.send_message(message.chat.id, msg_text, reply_markup=markup)
                    self.set_state(message.chat.id, self.ProductState.DEACTIVATE_CONFIRM)
                    self.bot.register_next_step_handler(message, self.deactivate_confirm)

                except Product.DoesNotExist:
                    self.bot.send_message(message.chat.id, t(message, "product_code_not_found"))
                    return
        except Exception as e:
            error_message = traceback.format_exc()  # دریافت Traceback کامل
            print(f"Error in handle_buttons: {e}\n{error_message}")

    def deactivate_confirm(self, message):
        try:
            state_manager = RedisStateManager(message.chat.id)

            # بازیابی کد محصول از Redis
            product_code = state_manager.get_user_data("product_code")
            if product_code:
                try:
                    product = Product.objects.get(code=product_code)
                    if message.text == t(message, "yes_im_sure"):
                        # حذف محصول از دیتابیس
                        if product.status:
                            product.status = False
                            product.save()
                        else:
                            product.status = True
                            product.save()

                        # ارسال پیام موفقیت‌آمیز به کاربر
                        main_menu = ProfileModel.objects.get(tel_id=message.from_user.id).tel_menu
                        extra_button_menu = ProfileModel.objects.get(tel_id=message.from_user.id).extra_button_menu
                        markup = send_menu(message, main_menu, "main menu", extra_button_menu)
                        action_text = t(message, "activated") if product.status else t(message, "deactivated")
                        self.bot.send_message(message.chat.id, t(message, "product_toggled", action=action_text), reply_markup=markup)

                    elif message.text == t(message, "cancel_action"):
                        self.cancle_request(message)
                        return

                    self.reset_state(message.chat.id)
                except Product.DoesNotExist:
                    self.bot.send_message(message.chat.id, t(message, "product_code_not_found"))
                    return
            else:
                self.bot.send_message(message.chat.id, "کد محصول ذخیره نشده است.")
                return
            
        except Exception as e:
            self.bot.send_message(message.chat.id, "خطایی رخ داده است. لطفاً دوباره تلاش کنید.")
            print(f"Error: {e}")

    def cancle_request(self, message):
        try:
            if subscription.subscription_offer(message):
                # بازیابی منوها از Redis
                state_manager = RedisStateManager(message.chat.id)
                main_menu = ProfileModel.objects.get(tel_id=message.from_user.id).tel_menu
                extra_button_menu = ProfileModel.objects.get(tel_id=message.from_user.id).extra_button_menu
                markup = send_menu(message, main_menu, "main menu", extra_button_menu)
                session_manager.reset_user_session(message.chat.id, namespace="menu")
                self.bot.send_message(message.chat.id, t(message, "home_message"), reply_markup=markup)
                self.reset_state(message.chat.id)
                return
        except Exception as e:
            self.bot.send_message(message.chat.id, "خطایی رخ داده است. لطفاً دوباره تلاش کنید.")
            print(f"Error: {e}")



############################  SEND PAYMENT LINK  ############################

def send_payment_link(app, context):
    chat_id = update.message.chat_id
    email = "example@test.com"  # ایمیل کاربر
    mobile = ProfileModel.objects.get(tel_id=chat_id).phone  # شماره موبایل کاربر
    amount = 100000  # مبلغ پرداخت
    description = "توضیحات کالا"

    # ساخت لینک پرداخت
    payment_url = f"http://intelleum.ir:8443/buy/{amount}/{description}/?email={email}&mobile={mobile}"

    return payment_url

############################  SEND PRODUCT MESSAGE  ############################

from telethon import Button
import traceback
from telethon.tl.types import InputMediaPhoto
from django.db import models
from django.core.cache import cache
import threading

@add_performance_monitoring_to_class
class ProductHandler:
    """مدیریت ارسال پیام و اطلاعات محصول - نسخه بهینه‌شده"""
    
    def __init__(self, app, product, current_site, photos=None, attributes=None):
        self.app = app
        self.product = product
        self.current_site = current_site
        self.user_manager = UserOrderManager()
        self.photos = photos or []
        self.attributes = attributes
        self._variants_data_cache = None

    def get_product_variants_data(self):
        """دریافت همه داده‌های واریانت در یک کوئری با کشینگ"""
        if self._variants_data_cache:
            return self._variants_data_cache
            
        cache_key = f"product_{self.product.id}_full_variants_data"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            self._variants_data_cache = cached_data
            return cached_data
        
        # بارگذاری بهینه با prefetch_related
        from products.models import ProductVariant
        
        variants = ProductVariant.objects.filter(
            product_id=self.product.id
        ).prefetch_related('values__option')
        
        variants_dict = {}
        variants_list = []
        
        for variant in variants:
            variant_data = {
                'id': variant.id,
                'sku': variant.sku,
                'stock': variant.stock,
                'price_override': variant.price_override,
                'values': {}
            }
            
            for option_value in variant.values.all():
                key = option_value.option.name.capitalize()
                value = option_value.value
                variant_data['values'][key] = value
                
                if key not in variants_dict:
                    variants_dict[key] = set()
                variants_dict[key].add(value)
            
            variants_list.append(variant_data)
        
        def sort_variant_values(values):
            numeric_values = []
            string_values = []
            
            for value in values:
                try:
                    numeric_values.append(float(value) if '.' in str(value) else int(value))
                except (ValueError, TypeError):
                    string_values.append(str(value))
            
            sorted_numeric = sorted(numeric_values)
            sorted_strings = sorted(string_values)
            
            return [str(val) for val in sorted_numeric] + sorted_strings

        result = {
            'variants_dict': {key: sort_variant_values(values) for key, values in variants_dict.items()},
            'variants_list': variants_list
        }
        
        cache.set(cache_key, result, timeout=300)
        self._variants_data_cache = result
        
        return result

    def get_variants_dict(self, variants=None):
        """تبدیل واریانت‌ها به دیکشنری - کاملاً از کش استفاده می‌کند"""
        variants_data = self.get_product_variants_data()
        return variants_data['variants_dict']

    def get_variant_by_selected_values(self, product, selected_values):
        """پیدا کردن واریانت بر اساس مقادیر انتخاب شده"""
        variants_data = self.get_product_variants_data()
        
        print(f"🔍 [VARIANT DEBUG] Looking for variant with: {selected_values}")
        print(f"🔍 [VARIANT DEBUG] Total variants: {len(variants_data['variants_list'])}")
        
        for variant_data in variants_data['variants_list']:
            variant_values = variant_data['values']
            
            # بررسی تطابق کامل
            match = True
            for key, selected_value in selected_values.items():
                variant_value = variant_values.get(key)
                
                if not variant_value:
                    match = False
                    break
                    
                selected_clean = str(selected_value).strip().lower()
                variant_clean = str(variant_value).strip().lower()
                
                if selected_clean != variant_clean:
                    match = False
                    break
            
            if match:
                print(f"✅ [VARIANT DEBUG] EXACT MATCH FOUND: {variant_data['id']}")
                from products.models import ProductVariant
                return ProductVariant.objects.get(id=variant_data['id'])
        
        print("❌ [VARIANT DEBUG] No exact matching variant found")
        return None

    def format_price(self):
        """فرمت‌بندی قیمت بدون کوئری دیتابیس"""
        formatted_price = "{:,.0f}".format(float(self.product.price))
        formatted_final_price = "{:,.0f}".format(float(self.product.final_price))

        if self.product.discount > 0:
            return (
                f"🏃 {self.product.discount} % تخفیف\n"
                f"💵 قیمت: <s>{formatted_price}</s> تومان ⬅ {formatted_final_price} تومان"
            )
        return f"💵 قیمت: {formatted_price} تومان"

    def generate_caption(self):
        """تولید کپشن محصول با بهینه‌سازی"""
        brand_text = f"🔖 برند کالا: {self.product.brand}\n" if self.product.brand else ""
        description_text = f"{self.product.description}\n" if self.product.description else ""

        # مشخصات کالا (Attributes)
        attribute_text = ""
        if self.attributes:
            attribute_text = "\n✅ ".join(
                [f"{attr.key}: {attr.value}" if attr.value else f"{attr.key}" for attr in self.attributes]
            )
            attribute_text = f"✅ {attribute_text}\n\n"

        # واریانت‌ها (Variants)
        variants_text = ""
        variants_data = self.get_product_variants_data()
        
        if variants_data['variants_dict']:
            variant_lines = [f"{key}: {', '.join(values)}" for key, values in variants_data['variants_dict'].items()]
            variants_text = "✅ " + "\n✅ ".join(variant_lines) + "\n\n"

        # متن نهایی کپشن
        return (
            f"\n⭕️ نام کالا: {self.product.name}\n"
            f"{brand_text}"
            f"کد کالا: {self.product.code}\n\n"
            f"{description_text}\n"
            f"{attribute_text}"
            f"{variants_text}"
            f"📫 ارسال به تمام نقاط کشور\n\n"
            f"{self.format_price()}\n"
        )

    async def send_product_channel(self, chat_id, buttons=True):
        """ارسال محصول در کانال - نسخه بهینه"""
        try:
            caption = self.generate_caption()
            
            if not self.photos:
                await self.app.send_message(
                    chat_id,
                    caption,
                    parse_mode="html",
                    buttons=[[Button.inline("🛒 همین حالا بخرش", b"buy_now")]] if buttons else None
                )
                return

            # ارسال سریع فقط اولین عکس
            files = self.photos[:1]  # فقط یک عکس
            input_file = await self.app.upload_file(files[0])
            
            await self.app.send_file(
                chat_id,
                input_file,
                caption=caption,
                parse_mode="html",
            )

            # دکمه در پس‌زمینه
            if buttons:
                self.app.send_message(
                    chat_id, 
                    "To see the comments on this product or make the purchase click", 
                    parse_mode="html", 
                    buttons=[[Button.inline("🛒 همین حالا بخرش", b"buy_now")]]
                )

        except Exception as e:
            print(f"⚠ خطا در ارسال محصول: {e}")

    def send_product_message(self, chat_id, buttons=True):
        """ارسال محصول با دکمه‌های سریع"""
        try:
            photos = [
                types.InputMediaPhoto(open(self.product.main_image.path, 'rb'), caption=self.generate_caption(), parse_mode='HTML')
            ] + [
                types.InputMediaPhoto(open(i.image.path, 'rb')) for i in self.product.images.all()
            ]
            
            print(photos)

            if len(photos) > 10:
                photos = photos[:10]

            self.app.send_media_group(chat_id, media=photos)
            
            # استفاده از نسخه سریع برای دکمه‌ها
            if buttons:
                self.send_buttons(chat_id)  # این حالا نسخه سریع است
                
        except Exception as e:
            error_message = traceback.format_exc()
            print(f"Error in send_product_message: {e}\n{error_message}")

    def send_buttons(self, chat_id):
        """ارسال سریع دکمه‌ها بدون تأخیر"""
        try:
            # محاسبه سریع داده‌های مورد نیاز
            buttons_data = self._prepare_buttons_data(chat_id)
            if not buttons_data:
                return
                
            # ارسال فوری دکمه‌ها
            self._send_buttons_from_data(chat_id, buttons_data)
            
        except Exception as e:
            print(f"Error in send_buttons: {e}")

    def _prepare_buttons_data(self, chat_id):
        """آماده‌سازی سریع داده‌های دکمه"""
        try:
            # دریافت session
            session = SessionManager()
            user_session = session.get_user_session(chat_id, namespace="variants")
            variant_states = user_session.get(str(self.product.code), {})
            
            # کوئری‌های موازی برای داده‌های ضروری
            profile = ProfileModel.objects.get(tel_id=chat_id)
            cart, _ = Cart.objects.get_or_create(profile=profile)
            
            # استفاده از داده‌های کش شده
            variants_dict = self.get_variants_dict(self.product.variants.all())
            
            # محاسبه سریع مقادیر انتخاب شده
            selected_values = {}
            for i, key in enumerate(variants_dict.keys()):
                if str(i) in variant_states:
                    values_list = list(variants_dict[key])
                    selected_index = variant_states[str(i)]
                    if selected_index < len(values_list):
                        selected_values[key] = values_list[selected_index]
            
            # پیدا کردن واریانت
            variant = None
            if selected_values:
                variant = self.get_variant_by_selected_values(self.product, selected_values)
            
            # وضعیت سبد خرید
            current_quantity = 0
            cart_item_exists = False
            
            if variant:
                cart_item = CartItem.objects.filter(
                    cart=cart, 
                    product=self.product, 
                    variant=variant
                ).first()
                if cart_item:
                    current_quantity = cart_item.quantity
                    cart_item_exists = True
            else:
                cart_item = CartItem.objects.filter(
                    cart=cart, 
                    product=self.product, 
                    variant__isnull=True
                ).first()
                if cart_item:
                    current_quantity = cart_item.quantity
                    cart_item_exists = True

            return {
                'variant_states': variant_states,
                'cart': cart,
                'variants_dict': variants_dict,
                'selected_values': selected_values,
                'variant': variant,
                'current_quantity': current_quantity,
                'cart_item_exists': cart_item_exists
            }
            
        except Exception as e:
            print(f"Error in _prepare_buttons_data: {e}")
            return None

    def _send_buttons_from_data(self, chat_id, buttons_data):
        """ارسال فوری دکمه‌ها با داده‌های از پیش محاسبه شده"""
        try:
            variant_states = buttons_data['variant_states']
            cart = buttons_data['cart']
            variants_dict = buttons_data['variants_dict']
            variant = buttons_data['variant']
            current_quantity = buttons_data['current_quantity']
            cart_item_exists = buttons_data['cart_item_exists']

            # ساخت سریع دکمه‌ها
            buttons = []
            handlers = {}
            
            if cart_item_exists:
                # حالت شمارنده
                buttons.extend([
                    ("➕", f"increase_{self.product.code}", 2),
                    (f"{current_quantity}", "count", 1),
                    ("➖", f"decrease_{self.product.code}", 0),
                ])
                
                handlers.update({
                    f"increase_{self.product.code}": self.handle_buttons,
                    f"decrease_{self.product.code}": self.handle_buttons,
                })
                
                # دکمه‌های واریانت
                for i, (key, values) in enumerate(variants_dict.items()):
                    current_index = variant_states.get(str(i), 0)
                    current_value = values[current_index] if current_index < len(values) else values[0]
                    
                    buttons.extend([
                        ("⏪", f"VarPrev_{self.product.code}_{i}", i * 3 + 3),
                        (f"{key}: {current_value}", f"var_{i}", i * 3 + 4),
                        ("⏩", f"VarNext_{self.product.code}_{i}", i * 3 + 5),
                    ])
                    
                    handlers.update({
                        f"VarPrev_{self.product.code}_{i}": self.handle_variant_navigation,
                        f"VarNext_{self.product.code}_{i}": self.handle_variant_navigation,
                    })

                # دکمه سبد خرید
                total_cart_items = cart.total_items()
                buttons.append((f"🛒 سبد خرید ({total_cart_items})", "view_cart", len(buttons) + 2))
                
                # لیآوت
                if variants_dict:
                    button_layout = [3] + [3] * len(variants_dict) + [1]
                else:
                    button_layout = [3, 1]
                    
            else:
                # حالت اولیه
                buttons.extend([
                    ("افزودن به 🛒", f"addtocart_{self.product.code}", 1),
                    ("نظرات 💭", f"comments_{self.product.code}", 0),
                ])
                
                handlers.update({
                    f"addtocart_{self.product.code}": self.handle_add_to_cart,
                    f"comments_{self.product.code}": self.handle_comments,
                })
                
                button_layout = [2]

            # متن اطلاع‌رسانی
            stock_info = variant.stock if variant else self.product.stock
            text = f"به هر تعداد در انبار موجود باشه می‌تونی سفارش بدی! (موجودی: {stock_info})"
            
            # ارسال فوری
            markup = SendMarkup(
                bot=self.app,
                chat_id=chat_id,
                text=text,
                buttons=buttons,
                button_layout=button_layout,
                handlers=handlers
            )
            markup.send()
            
        except Exception as e:
            print(f"Error in _send_buttons_from_data: {e}")

    def _send_buttons_safe(self, chat_id):
        """متد قدیمی برای سازگاری - حالا از نسخه سریع استفاده می‌کند"""
        self.send_buttons(chat_id)

    def show_initial_state(self, chat_id, message_id, product):
        """نمایش حالت اولیه"""
        try:
            buttons = [
                ("افزودن به 🛒", f"addtocart_{product.code}", 1),
                ("نظرات 💭", f"comments_{product.code}", 0),
            ]
            
            handlers = {
                f"addtocart_{product.code}": self.handle_add_to_cart,
                f"comments_{product.code}": self.handle_comments,
            }
            
            stock_info = product.stock
            text = f"به هر تعداد در انبار موجود باشه می‌تونی سفارش بدی! (موجودی: {stock_info})"

            markup = SendMarkup(
                bot=self.app,
                chat_id=chat_id,
                text=text,
                buttons=buttons,
                button_layout=[2],
                handlers=handlers,
            )
            
            markup.edit(message_id)

        except Exception as e:
            print(f"❌ Error in show_initial_state: {e}")

    def handle_add_to_cart(self, call):
        """مدیریت افزودن به سبد خرید"""
        try:
            data = call.data.split("_")
            product_code = str(data[-1])
            chat_id = call.message.chat.id
            message_id = call.message.message_id

            product = Product.objects.get(code=product_code)
            profile = ProfileModel.objects.get(tel_id=chat_id)
            cart, _ = Cart.objects.get_or_create(profile=profile)

            session = SessionManager()
            user_session = session.get_user_session(chat_id, namespace="variants")
            variant_states = user_session.get(str(product_code), {})

            variants_dict = self.get_variants_dict(product.variants.all())
            selected_values = {}
            
            for i, key in enumerate(variants_dict.keys()):
                if str(i) in variant_states:
                    values_list = list(variants_dict[key])
                    selected_index = variant_states[str(i)]
                    if selected_index < len(values_list):
                        selected_values[key] = values_list[selected_index]

            variant = None
            if selected_values:
                variant = self.get_variant_by_selected_values(product, selected_values)

            cart_item = None
            if variant:
                cart_item = CartItem.objects.filter(cart=cart, product=product, variant=variant).first()
            else:
                if not product.variants.exists():
                    cart_item = CartItem.objects.filter(cart=cart, product=product, variant__isnull=True).first()

            if not cart_item:
                cart_item = CartItem.objects.create(
                    cart=cart, 
                    product=product,
                    variant=variant,
                    quantity=0
                )

            self.update_product_message(chat_id, message_id, product, cart)
            self.app.answer_callback_query(call.id, "به سبد خرید اضافه شد")

        except Exception as e:
            print(f"❌ Error in handle_add_to_cart: {e}")

    def handle_buttons(self, call):
        """مدیریت دکمه‌های افزایش/کاهش"""
        try:
            data = call.data.split("_")
            action = data[0]
            product_code = str(data[1])
            chat_id = call.message.chat.id
            message_id = call.message.message_id

            product = Product.objects.get(code=product_code)
            profile = ProfileModel.objects.get(tel_id=chat_id)
            cart, _ = Cart.objects.get_or_create(profile=profile)

            session = SessionManager()
            user_session = session.get_user_session(chat_id, namespace="variants")
            variant_states = user_session.get(str(product_code), {})

            variants_dict = self.get_variants_dict(product.variants.all())
            selected_values = {}
            
            for i, key in enumerate(variants_dict.keys()):
                if str(i) in variant_states:
                    values_list = list(variants_dict[key])
                    selected_index = variant_states[str(i)]
                    if selected_index < len(values_list):
                        selected_values[key] = values_list[selected_index]

            variant = None
            if selected_values:
                variant = self.get_variant_by_selected_values(product, selected_values)

            cart_item = None
            if variant:
                cart_item = CartItem.objects.filter(cart=cart, product=product, variant=variant).first()
            else:
                if not product.variants.exists():
                    cart_item = CartItem.objects.filter(cart=cart, product=product, variant__isnull=True).first()

            should_show_initial = False

            if action == "increase":
                if not cart_item:
                    cart_item = CartItem.objects.create(
                        cart=cart, 
                        product=product,
                        variant=variant,
                        quantity=1
                    )
                else:
                    max_stock = variant.stock if variant else product.stock
                    if cart_item.quantity < max_stock:
                        cart_item.quantity += 1
                        cart_item.save()
                    else:
                        self.app.answer_callback_query(call.id, f"متاسفانه، بیشتر از {max_stock} عدد در انبار موجود نیست!", show_alert=True)
                        return
                        
            elif action == "decrease":
                if cart_item:
                    if cart_item.quantity > 1:
                        cart_item.quantity -= 1
                        cart_item.save()
                    elif cart_item.quantity == 1:
                        cart_item.quantity = 0
                        cart_item.save()
                    elif cart_item.quantity == 0:
                        cart_item.delete()
                        should_show_initial = True
                        self.app.answer_callback_query(call.id, "آیتم از سبد خرید حذف شد")
                else:
                    should_show_initial = True

            if should_show_initial:
                self.show_initial_state(chat_id, message_id, product)
            else:
                self.update_product_message(chat_id, message_id, product, cart)

        except Exception as e:
            print(f"Error in handle_buttons: {e}")

    def update_product_message(self, chat_id, message_id, product, cart):
        """آپدیت پیام محصول"""
        try:
            session = SessionManager()
            user_session = session.get_user_session(chat_id, namespace="variants")
            variant_states = user_session.get(str(product.code), {})
            
            variants_dict = self.get_variants_dict(product.variants.all())
            selected_values = {}
            
            for i, key in enumerate(variants_dict.keys()):
                if str(i) in variant_states:
                    values_list = list(variants_dict[key])
                    selected_index = variant_states[str(i)]
                    if selected_index < len(values_list):
                        selected_values[key] = values_list[selected_index]

            variant = None
            current_quantity = 0
            cart_item_exists = False
            
            if selected_values:
                variant = self.get_variant_by_selected_values(product, selected_values)

            cart_item = None
            if variant:
                cart_item = CartItem.objects.filter(cart=cart, product=product, variant=variant).first()
            else:
                if not product.variants.exists():
                    cart_item = CartItem.objects.filter(cart=cart, product=product, variant__isnull=True).first()

            if cart_item:
                current_quantity = cart_item.quantity
                cart_item_exists = True

            buttons = []
            handlers = {}

            # حالت شمارنده
            buttons.extend([
                ("➕", f"increase_{product.code}", 2),
                (f"{current_quantity}", "count", 1),
                ("➖", f"decrease_{product.code}", 0),
            ])
            
            handlers = {
                f"increase_{product.code}": self.handle_buttons,
                f"decrease_{product.code}": self.handle_buttons,
            }
            
            # دکمه‌های واریانت
            for i, (key, values) in enumerate(variants_dict.items()):
                current_index = variant_states.get(str(i), 0)
                current_value = values[current_index] if current_index < len(values) else values[0]
                
                buttons.extend([
                    ("⏪", f"VarPrev_{product.code}_{i}", i * 3 + 3),
                    (f"{key}: {current_value}", f"var_{i}", i * 3 + 4),
                    ("⏩", f"VarNext_{product.code}_{i}", i * 3 + 5),
                ])
                
                handlers[f"VarPrev_{product.code}_{i}"] = self.handle_variant_navigation
                handlers[f"VarNext_{product.code}_{i}"] = self.handle_variant_navigation

            # دکمه سبد خرید
            total_cart_items = cart.total_items()
            buttons.append((f"🛒 سبد خرید ({total_cart_items})", "view_cart", len(buttons) + 2))
            
            # لیآوت
            if variants_dict:
                button_layout = [3] + [3] * len(variants_dict) + [1]
            else:
                button_layout = [3, 1]

            stock_info = variant.stock if variant else product.stock
            text = f"به هر تعداد در انبار موجود باشه می‌تونی سفارش بدی! (موجودی: {stock_info})"

            markup = SendMarkup(
                bot=self.app,
                chat_id=chat_id,
                text=text,
                buttons=buttons,
                button_layout=button_layout,
                handlers=handlers,
            )
            
            markup.edit(message_id)

        except Exception as e:
            print(f"❌ Error in update_product_message: {e}")

    def handle_variant_navigation(self, call):
        """مدیریت ناوبری واریانت‌ها"""
        try:
            parts = call.data.split("_")
            action_type = parts[0]
            product_code = parts[1]
            variant_index = int(parts[2])

            chat_id = call.message.chat.id
            message_id = call.message.message_id

            profile = ProfileModel.objects.get(tel_id=chat_id)
            cart, _ = Cart.objects.get_or_create(profile=profile)

            session = SessionManager()
            user_session = session.get_user_session(chat_id, namespace="variants")
            variant_states = user_session.get(str(product_code), {})

            variants_dict = self.get_variants_dict(self.product.variants.all())
            variant_keys = list(variants_dict.keys())

            if variant_index >= len(variant_keys):
                self.app.answer_callback_query(call.id, "خطا در یافتن واریانت!", show_alert=True)
                return

            current_key = variant_keys[variant_index]
            values = list(variants_dict[current_key])
            current_state = variant_states.get(str(variant_index), 0)

            if action_type == "VarPrev":
                current_state = (current_state - 1) % len(values)
            elif action_type == "VarNext":
                current_state = (current_state + 1) % len(values)

            variant_states[str(variant_index)] = current_state
            user_session[str(product_code)] = variant_states
            session.set_user_session(chat_id, user_session, namespace="variants")

            self.update_product_message(chat_id, message_id, self.product, cart)
            
            current_value = values[current_state]
            self.app.answer_callback_query(call.id, f"{current_key} به {current_value} تغییر کرد")

        except Exception as e:
            print(f"Error in handle_variant_navigation: {e}")
            self.app.answer_callback_query(call.id, "خطا در تغییر واریانت!", show_alert=True)

    def handle_comments(self, call):
        """مدیریت دکمه نظرات"""
        try:
            chat_id = call.message.chat.id
            self.app.send_message(chat_id, "صفحه نظرات محصول...")
            self.app.answer_callback_query(call.id)
        except Exception as e:
            print(f"Error in handle_comments: {e}")


############################  SEND CART  ############################    
from collections import OrderedDict
import traceback

class SendCart:
 
    def __init__(self, app, message):
        try:
            self.app = app
            self.chat_id = message.chat.id
            self.session = CartSessionManager(self.chat_id)  # اضافه کردن CartSessionManager
            self.profile = ProfileModel.objects.get(tel_id=self.chat_id)
            self.cart = Cart.objects.filter(profile=self.profile).first()
            if self.cart:
                self.cart.items.filter(quantity=0).delete()
            self.current_site = 'https://intelleum.ir:8443'


            if not self.cart:
                
                try:
                    if hasattr(message, "message_id") and hasattr(message, "text"):  
                        # یعنی از طرف کاربر پیام متنی اومده
                        self.app.send_message(
                            chat_id=message.chat.id,
                            text=t(message, "cart_empty")
                        )
                    else:
                        # یعنی از طرف callback_query اومده (دکمه فشرده شده)
                        self.app.edit_message_text(
                            chat_id=message.message.chat.id,
                            message_id=message.message.message_id,
                            text=t(message, "cart_empty"),
                            reply_markup=None
                        )
                    self.cart = None
                    return
                except Exception as e:
                    print(f"{e}")
            self.total_price = sum(item.total_price() for item in self.cart.items.all())
            self.text = f"🛒 سبد خرید شما:\n\n💰 مجموع مبلغ قابل پرداخت:\t{self.total_price:,.0f} تومان"

            # بازیابی دکمه‌های قبلی اگر وجود داشته باشند
            stored_buttons = self.session.get_buttons()

            self.buttons = OrderedDict()


            # اگر دکمه‌ها قبلاً تنظیم نشده باشند، آن‌ها را مقداردهی اولیه می‌کنیم
            if not self.buttons and self.cart:
                for index, item in enumerate(self.cart.items.all(), start=1):
                    title = f"{item.product.name} × {item.quantity} \t\t\t\t▼"
                    self.buttons[title] = (f"product_show_{item.product.code}", index)

                self.buttons["✅ تکمیل خرید و پرداخت"] = ("confirm order", len(self.buttons) + 1)



            self.markup = SendMarkup(
                bot=self.app,
                chat_id=self.chat_id,
                text=self.text,
                buttons=self.buttons,
                button_layout=[1] * len(self.buttons),
                handlers={
                    "confirm order": self.invoice,
                    **{f"product_show_{item.product.code}": self.handle_buttons for item in self.cart.items.all()}
                }
            )
        except Exception as e:
            print(f"Error in __init__: {e}\n{traceback.format_exc()}")


    def handle_buttons(self, call):
        """مدیریت دکمه‌های افزایش و کاهش سفارش"""
        try:
            data = call.data.split("_")
            action = data[0]
            product_code = str(data[1]) if len(data) > 1 else None
            chat_id = call.message.chat.id
            message_id = call.message.message_id

            if not product_code:
                return

            print("Action:", action, "Product Code:", product_code)
            product = Product.objects.get(code=product_code)
            profile = ProfileModel.objects.get(tel_id=chat_id)
            cart, _ = Cart.objects.get_or_create(profile=profile)

            # دریافت وضعیت واریانت‌های انتخاب شده از session
            session = SessionManager()
            user_session = session.get_user_session(chat_id, namespace="variants")
            variant_states = user_session.get(str(product_code), {})

            # ساخت دیکشنری مقادیر انتخاب شده
            variants_dict = self.get_variants_dict(product.variants.all())
            selected_values = {}
            
            for i, key in enumerate(variants_dict.keys()):
                if str(i) in variant_states:
                    values_list = list(variants_dict[key])
                    selected_index = variant_states[str(i)]
                    if selected_index < len(values_list):
                        selected_values[key] = values_list[selected_index]

            print(f"🔍 [DEBUG] Selected values for action: {selected_values}")

            # پیدا کردن واریانت دقیق
            variant = None
            if selected_values:
                variant = self.get_variant_by_selected_values(product, selected_values)
                print(f"🔍 [DEBUG] Found exact variant for action: {variant}")

            # پیدا کردن CartItem دقیق برای این واریانت
            cart_item = None
            if variant:
                cart_item = CartItem.objects.filter(cart=cart, product=product, variant=variant).first()
            else:
                if not product.variants.exists():
                    cart_item = CartItem.objects.filter(cart=cart, product=product, variant__isnull=True).first()

            if action == "increase":
                if not cart_item:
                    # اگر CartItem وجود ندارد، ایجاد کن
                    cart_item = CartItem.objects.create(
                        cart=cart, 
                        product=product,
                        variant=variant,
                        quantity=1
                    )
                    print(f"🔍 [DEBUG] Created new CartItem with quantity: 1")
                else:
                    # افزایش تعداد
                    max_stock = variant.stock if variant else product.stock
                    if cart_item.quantity < max_stock:
                        cart_item.quantity += 1
                        cart_item.save()
                        print(f"Increased to: {cart_item.quantity}")
                    else:
                        self.app.answer_callback_query(call.id, f"متاسفانه، بیشتر از {max_stock} عدد در انبار موجود نیست!", show_alert=True)
                        return
                        
            elif action == "decrease":
                if cart_item:
                    print(f"Decreasing from: {cart_item.quantity}")
                    if cart_item.quantity > 1:
                        # کاهش عادی - از 2 به 1، از 3 به 2 و ...
                        cart_item.quantity -= 1
                        cart_item.save()
                        print(f"Decreased to: {cart_item.quantity}")
                    elif cart_item.quantity == 1:
                        # کاهش از 1 به 0
                        cart_item.quantity = 0
                        cart_item.save()
                        print("Decreased to 0")
                    elif cart_item.quantity == 0:
                        # کاهش از 0 - حذف CartItem و رفتن به حالت اولیه
                        cart_item.delete()
                        print("Deleted cart item - returning to initial state")
                        # 🔥 اینجا باید به حالت اولیه برگردیم
                        self.app.answer_callback_query(call.id, "آیتم از سبد خرید حذف شد")
                else:
                    # اگر CartItem وجود ندارد و کاربر - زده، یعنی می‌خواهد به حالت اولیه برگردد
                    print("No cart item exists - already in initial state")

            # آپدیت پیام با وضعیت جدید
            self.update_product_message(chat_id, message_id, product, cart)

        except Exception as e:
            error_message = traceback.format_exc()
            print(f"Error in handle_buttons: {e}\n{error_message}")



    def send(self, message_or_call):
        try:
            # حذف آیتم‌هایی که تعدادشان صفر شده است
            if self.cart:
                self.cart.items.filter(quantity=0).delete()

            if not self.cart or not self.cart.items.exists():
                # تشخیص نوع ورودی
                if isinstance(message_or_call, types.Message):
                    # ورودی از نوع Message
                    self.app.send_message(
                        chat_id=message_or_call.chat.id,
                        text=t(message_or_call, "cart_empty"),
                    )
                elif isinstance(message_or_call, types.CallbackQuery):
                    # ورودی از نوع CallbackQuery - همیشه پیام جدید
                    self.app.send_message(
                        chat_id=message_or_call.message.chat.id,
                        text=t(message_or_call.message, "cart_empty"),
                    )
                self.cart = None
                return

            # بقیه کد برای زمانی که سبد خرید خالی نیست
            self.total_price = sum(item.total_price() for item in self.cart.items.all())
            self.text = f"🛒 سبد خرید شما:\n\n💰 مجموع مبلغ قابل پرداخت:\t{self.total_price:,.0f} تومان"

            # به‌روزرسانی دکمه‌ها پس از حذف آیتم‌های صفر شده
            self.buttons = OrderedDict()
            for index, item in enumerate(self.cart.items.all(), start=1):
                title = f"{item.product.name} × {item.quantity} \t\t\t\t▼"
                self.buttons[title] = (f"product_show_{item.product.code}", index)

            self.buttons["✅ تکمیل خرید و پرداخت"] = ("confirm order", len(self.buttons) + 1)

            self.session.set_buttons(self.buttons)  # ذخیره دکمه‌ها در سشن
            self.session.update_buttons(self.buttons)
            
            # همیشه پیام جدید ارسال شود - بدون ویرایش پیام قبلی
            self.markup.send()

        except Exception as e:
            print(f"Error in send: {e}\n{traceback.format_exc()}")



    def add(self, call):
        try:
            data = call.data.split("_")
            action = data[0]  # increase یا decrease
            product_code = str(data[1]) if len(data) > 1 else None
            product = Product.objects.get(code=product_code)
            profile = ProfileModel.objects.get(tel_id=call.message.chat.id)
            cart = Cart.objects.get(profile=profile)

            try:
                cart_item = CartItem.objects.get(cart=cart, product=product)
            except CartItem.DoesNotExist:
                self.app.answer_callback_query(call.id, "این محصول دیگر در سبد خرید شما نیست!", show_alert=True)
                return  # ادامه اجرای تابع متوقف شود


            if action == "increase":
                if cart_item.quantity < product.stock:  # جلوگیری از سفارش بیش از موجودی
                    cart_item.quantity += 1
                else:
                    self.app.answer_callback_query(call.id, f"متاسفانه، بیشتر از {product.stock} عدد در انبار فروشگاه موجود نیست!", show_alert=True)
            elif action == "decrease" and cart_item.quantity > 1:
                cart_item.quantity -= 1
            cart_item.save()

            # دریافت دکمه‌های ذخیره‌شده از سشن
            stored_buttons = self.session.get_buttons()

            # بررسی اینکه کدام دکمه باز است (فلش بالا `▲` دارد)
            currently_open = next((key for key in stored_buttons.keys() if key.endswith("▲")), None)

            # ساخت دکمه‌های جدید
            new_buttons = OrderedDict()
            new_layout = []

            for key, value in stored_buttons.items():
                if key == currently_open:
                    # به‌روزرسانی تعداد محصول در دکمه باز
                    new_title = f"{product.name} × {cart_item.quantity} \t\t\t\t▲"
                    new_buttons[new_title] = value
                    new_layout.append(1)

                    # دکمه‌های افزایش، کاهش و حذف را حفظ می‌کنیم
                    new_buttons["❌"] = (f"remove_{product_code}_cart", value[1] + 1)
                    new_buttons["➖"] = (f"decrease_{product_code}_cart", value[1] + 1)
                    new_buttons["➕"] = (f"increase_{product_code}_cart", value[1] + 1)
                    new_layout.append(3)

                elif key not in ["❌", "➖", "➕"]:
                    # سایر دکمه‌ها را بدون تغییر نگه می‌داریم
                    new_buttons[key] = value
                    new_layout.append(1)

            # به‌روزرسانی مجموع قیمت
            self.total_price = sum(item.total_price() for item in self.cart.items.all())
            self.text = f"🛒 سبد خرید شما:\n\n💰 مجموع مبلغ قابل پرداخت:\t{self.total_price:,.0f} تومان"

            # ذخیره دکمه‌های جدید در سشن
            self.session.update_buttons(new_buttons)

            # ویرایش پیام و دکمه‌ها
            self.markup.text = self.text
            self.markup.buttons = new_buttons
            self.markup.button_layout = new_layout
            self.markup.edit(call.message.message_id)

        except Exception as e:
            print(f"Error in add: {e}\n{traceback.format_exc()}")


    def remove_item(self, call):
        try:
            product_code = call.data.split("_")[-2]
            profile = ProfileModel.objects.get(tel_id=call.message.chat.id)
            cart = Cart.objects.get(profile=profile)

            # حذف کامل آیتم از سبد خرید
            cart.items.filter(product__code=product_code).delete()

            # دریافت دکمه‌های ذخیره‌شده از سشن
            stored_buttons = self.session.get_buttons()

            # حذف دکمه محصول و دکمه‌های مرتبط (`❌`، `➖`، `➕`)
            new_buttons = OrderedDict()
            new_layout = []

            for key, value in stored_buttons.items():
                # بررسی اینکه آیا دکمه مربوط به این محصول است یا یکی از دکمه‌های کنترل آن
                if product_code in value[0]:
                    continue  # دکمه حذف شود

                new_buttons[key] = value
                new_layout.append(1)



            # به‌روزرسانی مجموع مبلغ قابل پرداخت
            self.total_price = sum(item.total_price() for item in cart.items.all())

            if cart.items.exists():
                self.text = f"🛒 سبد خرید شما:\n\n💰 مجموع مبلغ قابل پرداخت:\t{self.total_price:,.0f} تومان"
            else:
                self.text = t(call.message, "cart_empty")
                new_buttons = OrderedDict()  # تمام دکمه‌ها حذف شوند

            # ذخیره دکمه‌های جدید در سشن
            self.session.update_buttons(new_buttons)

            # ویرایش پیام و دکمه‌ها
            self.markup.text = self.text
            self.markup.buttons = new_buttons
            self.markup.button_layout = [1] * len(new_buttons)
            self.markup.edit(call.message.message_id)

        except Exception as e:
            print(f"Error in remove_item: {e}\n{traceback.format_exc()}")


    def invoice(self, update):
        try:
            # تشخیص نوع ورودی
            if isinstance(update, types.CallbackQuery):
                chat_id = update.message.chat.id
                message_id = update.message.message_id
                is_callback = True
            elif isinstance(update, types.Message):
                chat_id = update.chat.id
                message_id = update.message_id
                is_callback = False
            else:
                print("❌ update type not supported in invoice()")
                return

            profile = ProfileModel.objects.get(tel_id=chat_id)
            cart = Cart.objects.get(profile=profile)
            cart_items = CartItem.objects.filter(cart=cart)

            total_price = sum(item.total_price() for item in cart_items)

            invoice_text = "📜 <b>فاکتور سفارش شما</b>\n\n"
            for index, item in enumerate(cart_items, start=1):
                invoice_text += f"{index}) {item.product.name}  -  "
                invoice_text += f"{item.product.final_price:,.0f} x {item.quantity}\n\n"
            invoice_text += f"🧮 <b>مجموع کل:</b> {total_price:,.0f} تومان"

            address = Address.objects.filter(profile=profile, shipping_is_active=True).first()
            try:
                line1 = address.shipping_line1[:10] + '...' if len(address.shipping_line1)>10 else address.shipping_line1
            except Exception as e:
                line1 = ''
            address_text = (f"{line1}, {address.shipping_city_name}, {address.shipping_province_name}, {address.shipping_country_name}"
                            if address else ' --- ')
            if len(address_text)>40:
                address_text = address_text[:40] + "..."
                
            phone_text = (f"{profile.phone}" if profile.phone else ' --- ')

            payment_link = self.pay(update)

            buttons = {
                f"آدرس: {address_text}": {"callback_data": "address", "index": 1},
                f"شماره تماس: {phone_text}": {"callback_data": "phone", "index": 2},
                "پرداخت": {"url": payment_link, "index": 3} if address and profile.phone else {"callback_data": "phone_address_required", "index": 3},
            }

            self.markup = SendMarkup(
                bot=self.app,
                chat_id=chat_id,
                text=invoice_text,
                buttons=buttons,
                button_layout=[1, 1, 1],
                handlers={
                    "address": lambda call: SendLocation(self.app, call.message).show_addresses(),
                    "phone_address_required": lambda call: self.app.answer_callback_query(call.id, "⚠️ لطفاً ابتدا آدرس و شماره تماس را تکمیل کنید.")
                }
            )

            if isinstance(update, types.CallbackQuery):
                self.markup.edit(message_id)
            elif isinstance(update, types.Message):
                self.markup.send()

            if is_callback:
                self.app.answer_callback_query(update.id, "✅ در حال پردازش پرداخت ...")

        except Exception as e:
            print(f"Error in invoice: {e}\n{traceback.format_exc()}")
            self.app.send_message(chat_id, "❌ خطایی در نمایش فاکتور رخ داد.")

    def pay(self, update):

        # تشخیص نوع ورودی
        if isinstance(update, types.CallbackQuery):
            chat_id = update.message.chat.id
            message_id = update.message.message_id
            is_callback = True
        elif isinstance(update, types.Message):
            chat_id = update.chat.id
            message_id = update.message_id
            is_callback = False
        else:
            print("❌ update type not supported in invoice()")
            return


        # 2. ایجاد شناسه یکتا برای پرداخت
        payment_id = str(uuid.uuid4())

        # 3. ذخیره داده در کش
        cache.set(
            f'payment_{payment_id}',
            {'tel_id': chat_id},
            timeout=settings.PAYMENT_LINK_TIMEOUT
        )

        # 4. ساخت لینک پرداخت
        payment_link = f"{self.current_site}/buy?pid={payment_id}"

        return payment_link


        # ارسال درخواست به سرور شما
        # try:
        # 	response = requests.post(
        # 		f"{self.current_site}/buy",
        # 		headers={"Content-Type": "application/json"},
        # 		data=json.dumps({'tel_id': tel_id}),
        # 		verify=False
        # 	)
        # 	if response.status_code == 400:
        # 		self.app.send_message(
        # 				chat_id=call.message.chat.id,
        # 				text=f"roror:\n{response.error}"
        # 			)
        # 	# بررسی پاسخ سرور
        # 	if response.status_code == 200:
        # 		payment_data = response.json()
        # 		payment_link = payment_data.get("redirect_url")

        # 		if payment_link:
        # 			# ارسال لینک به کاربر در تلگرام
        # 			self.app.send_message(
        # 				chat_id=call.message.chat.id,
        # 				text=f"لینک پرداخت شما:\n{payment_link}"
        # 			)
        # 		else:
        # 			self.app.send_message(
        # 				chat_id=call.message.chat.id,
        # 				text="خطا در دریافت لینک پرداخت"
        # 			)
        # 	else:
        # 		self.app.send_message(
        # 			chat_id=call.message.chat.id,
        # 			text=f"خطا در ارتباط با سرور پرداخت: {response.status_code}"
        # 		)

        # except requests.exceptions.RequestException as e:
        # 	self.app.send_message(
        # 		chat_id=call.message.chat.id,
        # 		text=f"خطا در ارسال درخواست پرداخت: {str(e)}"
        # 	)
############################  SEND LOCATION  ############################

class SendLocation:
    def __init__(self, app, message_or_call):
        """
        مقداردهی اولیه کلاس
        :param app: شیء بات
        :param message_or_call: می‌تواند Message یا CallbackQuery باشد
        """
        try:
            self.app = app
            self.session_manager = session_manager
            self.user_id = (message_or_call.from_user.id if hasattr(message_or_call, 'from_user') else message_or_call.message.from_user.id)
            self.chat_id = message_or_call.chat.id if hasattr(message_or_call, 'chat') else message_or_call.message.chat.id
            self.message = message_or_call if isinstance(message_or_call, types.Message) else message_or_call.message
            self.profile = ProfileModel.objects.get(tel_id=self.chat_id)
            self.user_addresses = Address.objects.filter(profile=self.profile)
            self.active_address = Address.objects.filter(profile=self.profile, shipping_is_active=True).first()
        except Exception as e:
            error_details = traceback.format_exc()
            custom_message = f"Error in SendLocation init: {e}\nDetails:\n{error_details}"
            print(custom_message)
            self.app.send_message(self.chat_id, "خطایی در دریافت اطلاعات آدرس رخ داد")

    def show_addresses(self, call=None):
        """
        نمایش لیست آدرس‌های کاربر
        :param call: در صورتی که از طریق callback فراخوانی شده باشد
        """
        try:
            # متن پیام
            text = "📍 آدرس‌های شما:\n\n"

            # ساخت دکمه‌های آدرس‌ها
            buttons = {}

            for i, address in enumerate(self.user_addresses, start=1):
                line1 = address.shipping_line1[:15] + '...' if len(address.shipping_line1)>15 else address.shipping_line1
                btn_text = f"{i}. {line1}, {address.shipping_city_name}, {address.shipping_province_name}, {address.shipping_country_name}"
                if len(btn_text)>40:
                    btn_text = btn_text[:40] + "..."
                if address == self.active_address:
                    btn_text += " ⭐️"  # نشانگر آدرس فعال
                buttons[btn_text] = (f"show_address_{address.id}", i)

            # دکمه‌های پایه
            buttons["➕ افزودن آدرس جدید"] = ("add_new_address", len(buttons)+1)
            buttons["❌ بستن"] = ("close_addresses", len(buttons)+2)

            handlers = {
                "add_address": self.handle_add_address,
                "close_address": self.handle_close,
            }

            # اضافه کردن هندلرهای آدرس‌ها
            for address in self.user_addresses:
                handlers[f"address_{address.id}"] = lambda addr, c=address: self.show_single_address(addr, c)

            # ایجاد کیبورد
            markup = SendMarkup(
                bot=self.app,
                chat_id=self.chat_id,
                text=text,
                buttons=buttons,
                button_layout=[1]*len(self.user_addresses) + [2],
                handlers=handlers
            )

            # ارسال یا ویرایش پیام
            if call:
                markup.edit(call.message.message_id)  # ویرایش پیام موجود
            else:
                markup.send()  # ارسال پیام جدید

        except Exception as e:
            error_details = traceback.format_exc()
            print(f"Error in show_addresses: {e}\n{error_details}")
            self.app.send_message(self.chat_id, "خطایی در نمایش آدرس‌ها رخ داد")

    def show_single_address(self, address, call=None):
        """
        نمایش جزئیات یک آدرس خاص
        :param call: شیء callback
        :param address: آدرس انتخابی
        """
        try:
            # متن پیام
            text = f"📍 آدرس انتخابی:\n\n{address.shipping_line1}\n"
            text += f"🏙 شهر: {address.shipping_city_name}\n"
            text += f"🏛 استان: {address.shipping_province_name}\n"
            text += f"🌍 کشور: {address.shipping_country_name}\n"
            text += f"📮 کد پستی: {address.shipping_zip_code or 'ثبت نشده'}"

            # دکمه‌های مدیریت
            buttons = {
                "🗺 تغییر موقعیت مکانی": (f"change_location_{address.id}", 1),
                "ارسال خرید ها به این آدرس": (f"select_address_{address.id}", 2),
                "✏️ تغییر آدرس": (f"change_address_{address.id}", 3),
                "📝 تغییر کد پستی": (f"change_postal_{address.id}", 4),
                "🔙 بازگشت": ("back_to_addresses", 5),
                "🗑 حذف آدرس": (f"delete_address_{address.id}", 6)
            }

            markup = SendMarkup(
                bot=self.app,
                chat_id=self.chat_id,
                text=text,
                buttons=buttons,
                button_layout=[1, 1, 1, 1, 2],
                handlers={
                    f"change_location_{address.id}": lambda c: self.change_location(c, address),
                    f"select_address_{address.id}": lambda c: self.select_address(c, address),
                    f"change_address_{address.id}": lambda c: self.change_address_text(c, address),
                    f"change_postal_{address.id}": lambda c: self.change_postal(c, address),
                    "back_to_addresses": lambda c: self.show_addresses(c),
                    f"delete_address_{address.id}": lambda c: self.delete_address(c, address)
                }
            )

            # ارسال یا ویرایش پیام
            if call:
                markup.edit(call.message.message_id)  # ویرایش پیام موجود
            else:
                markup.send()  # ارسال پیام جدید

        except Exception as e:
            error_details = traceback.format_exc()
            print(f"Error in show_single_address: {e}\n{error_details}")
            self.app.send_message(self.chat_id, "خطایی در نمایش آدرس رخ داد")

    # --- متدهای مدیریت عملیات ---

    def handle_add_address(self, call):
        """افزودن آدرس جدید"""
        try:
            self.app.send_message(call.message.chat.id, "لطفاً آدرس جدید را ارسال کنید:")
            # اینجا می‌توانید از register_next_step_handler استفاده کنید
        except Exception as e:
            print(f"Error in handle_add_address: {e}")
            self.app.send_message(call.message.chat.id, "خطایی در افزودن آدرس رخ داد")

    def handle_close(self, call):
        """بستن پنجره آدرس‌ها"""
        try:
            self.app.delete_message(call.message.chat.id, call.message.message_id)
            self.session_manager.reset_user_session(call.message.chat.id, namespace="address")
        except Exception as e:
            print(f"Error in handle_close: {e}")

    def change_location(self, call, address):
        """تغییر موقعیت مکانی"""
        try:
            self.app.send_message(call.message.chat.id,
                                  "لطفاً موقعیت مکانی جدید را ارسال کنید:",
                                  reply_markup=types.ReplyKeyboardMarkup(
                                      resize_keyboard=True
                                  ).add(types.KeyboardButton("اشتراک گذاری موقعیت", request_location=True)))
            # ذخیره آدرس برای مرحله بعد
            # اینجا می‌توانید از register_next_step_handler استفاده کنید
        except Exception as e:
            print(f"Error in change_location: {e}")
            self.app.send_message(call.message.chat.id, "خطایی در تغییر موقعیت رخ داد")


    def delete_address(self, call, address):
        """حذف آدرس"""
        try:
            address.delete()
            self.app.answer_callback_query(call.id, "آدرس با موفقیت حذف شد")
            self.show_addresses(call)
        except Exception as e:
            print(f"Error in delete_address: {e}")
            self.app.answer_callback_query(call.id, "خطا در حذف آدرس")

    def add_new_address(self, call):
        try:

            text = "نحوه وارد کردن آدرس را انتخاب کنید"


            buttons = {
                "وارد کردن دستی": (f"manual_add_address", 1),
                "ارسال موقعیت مکانی": (f"send_location_add_address", 2),
            }

            handlers = {
                "manual_add_address": self.manual_add_address,
                "send_location_add_address": self.send_location_add_address,
            }

            data = self.session_manager.get_user_session(call.message.chat.id, namespace="address")
            data["state"] = "add_new_address"
            self.session_manager.set_user_session(call.message.chat.id, data, namespace="address")



            # ایجاد کیبورد
            markup = SendMarkup(
                bot=self.app,
                chat_id=self.chat_id,
                text=text,
                buttons=buttons,
                button_layout=[2],
                handlers=handlers
            )

            markup.edit(call.message.message_id)

        except Exception as e:
            error_details = traceback.format_exc()
            print(f"Error in add_new_address: {e}\n{error_details}")
            self.app.send_message(self.chat_id, "خطایی در نمایش آدرس‌ها رخ داد")

    def manual_add_address(self, call):
        try:
            text = "ساکن کدام کشور هستید؟"
            items = [item for item in get_country_choices(self.profile.lang)]
            items_name = [item[1] for item in get_country_choices(self.profile.lang)]
            items_code = [item[0] for item in get_country_choices(self.profile.lang)]
            paginator = InlineKeyboardPaginator(user_id=self.user_id, items=items_name, per_page=24, row_size=3, remember_last_page=True)
            buttons, layout = paginator.get_buttons_for_sendmarkup()

            handlers = {"prev": self.handle_prev, "next": self.handle_next}

            for code, country in items:
                if country in buttons:
                    buttons[country]["callback_data"] = f"country_{code}"
                    handlers[f'country_{code}'] = self.handle_picked_country

            buttons['🔙'] = {'callback_data': '_back', 'index': len(buttons)+1}
            handlers["_back"] = self.handle_previous

            buttons['❌ بستن'] = {'callback_data': 'address_close', 'index': len(buttons)+2}
            handlers["address_close"] = self.handle_close
            layout.append(2)


            data = self.session_manager.get_user_session(call.message.chat.id, namespace="address")
            data["state"] = "address_selection_country"
            self.session_manager.set_user_session(call.message.chat.id, data, namespace="address")



            # ایجاد کیبورد
            markup = SendMarkup(
                bot=self.app,
                chat_id=self.chat_id,
                text=text,
                buttons=buttons,
                button_layout=layout,
                handlers=handlers
            )


            markup.edit(call.message.message_id)

            print(self.session_manager.get_user_session(call.message.chat.id, namespace="address"))


        except Exception as e:
            error_details = traceback.format_exc()
            print(f"Error in show_addresses: {e}\n{error_details}")
            self.app.send_message(self.chat_id, "خطایی در نمایش آدرس‌ها رخ داد")


    def handle_prev(self, call):
        try:
            session = self.session_manager.get_user_session(call.message.chat.id, namespace="address")
            print(self.session_manager.get_user_session(call.message.chat.id, namespace="address"))

            paginator = InlineKeyboardPaginator.load_from_redis(self.user_id)
            paginator.prev_page()
            handlers = {"prev": self.handle_prev, "next": self.handle_next}
            if session['state'] == "address_selection_country":
                text = "ساکن کدام کشور هستید؟"
                items = [item for item in get_country_choices(self.profile.lang)]
                buttons, layout = paginator.get_buttons_for_sendmarkup()
                for code, country in items:
                    if country in buttons:
                        buttons[country]["callback_data"] = f"country_{code}"
                        handlers[f'country_{code}'] = self.handle_picked_country

            elif session['state'] == "address_selection_province":
                text = "ساکن کدام استان هستید؟"
                items = [item for item in get_province_choices(session["selected_country"], self.profile.lang)]
                buttons, layout = paginator.get_buttons_for_sendmarkup()
                for code, province in items:
                    if province in buttons:
                        buttons[province]["callback_data"] = f"province_{code}"
                        handlers[f'province_{code}'] = self.handle_picked_province

            elif session['state'] == "address_selection_city":
                text = "ساکن کدام شهر هستید؟"
                items = [item for item in get_city_choices(session["selected_country"], session["selected_province"], self.profile.lang)]
                buttons, layout = paginator.get_buttons_for_sendmarkup()
                for code, city in items:
                    if city in buttons:
                        buttons[city]["callback_data"] = f"city_{code}"
                        handlers[f'city_{code}'] = self.handle_picked_city
            
            buttons['🔙'] = {'callback_data': '_back', 'index': len(buttons)+1}
            handlers["_back"] = self.handle_previous

            buttons['❌ بستن'] = {'callback_data': 'address_close', 'index': len(buttons)+2}
            handlers["address_close"] = self.handle_close
            layout.append(2)


            SendMarkup(bot=self.app, chat_id=self.chat_id, text=text, buttons=buttons, button_layout=layout, handlers=handlers).edit(
                call.message.message_id)
            print(self.session_manager.get_user_session(call.message.chat.id, namespace="address"))

        except Exception as e:
            error_details = traceback.format_exc()
            print(f"Error in show_addresses: {e}\n{error_details}")
            self.app.send_message(self.chat_id, "خطایی در نمایش آدرس‌ها رخ داد")

    def handle_next(self, call):
        try:
            data = self.session_manager.get_user_session(call.message.chat.id, namespace="address")
            paginator = InlineKeyboardPaginator.load_from_redis(self.user_id)
            paginator.next_page()
            handlers = {"prev": self.handle_prev, "next": self.handle_next}
            if data['state'] == "address_selection_country":
                text = "ساکن کدام کشور هستید؟"
                items = [item for item in get_country_choices(self.profile.lang)]
                buttons, layout = paginator.get_buttons_for_sendmarkup()
                for code, country in items:
                    if country in buttons:
                        buttons[country]["callback_data"] = f"country_{code}"
                        handlers[f'country_{code}'] = self.handle_picked_country

            elif data['state'] == "address_selection_province":
                text = "ساکن کدام استان هستید؟"
                items = [item for item in get_province_choices(data["selected_country"], self.profile.lang)]
                buttons, layout = paginator.get_buttons_for_sendmarkup()
                for code, province in items:
                    if province in buttons:
                        buttons[province]["callback_data"] = f"province_{code}"
                        handlers[f'province_{code}'] = self.handle_picked_province

            elif data['state'] == "address_selection_city":
                text = "ساکن کدام شهر هستید؟"
                items = [item for item in get_city_choices(data["selected_country"], data["selected_province"], self.profile.lang)]
                buttons, layout = paginator.get_buttons_for_sendmarkup()
                for code, city in items:
                    if city in buttons:
                        buttons[city]["callback_data"] = f"city_{code}"
                        handlers[f'city_{code}'] = self.handle_picked_city
            
            buttons['🔙'] = {'callback_data': '_back', 'index': len(buttons)+1}
            handlers["_back"] = self.handle_previous

            buttons['❌ بستن'] = {'callback_data': 'address_close', 'index': len(buttons)+2}
            handlers["address_close"] = self.handle_close
            layout.append(2)


            SendMarkup(bot=self.app, chat_id=call.message.chat.id, text=text, buttons=buttons, button_layout=layout, handlers=handlers).edit(call.message.message_id)
            data = self.session_manager.get_user_session(call.message.chat.id, namespace="address")
            print(data)

        except Exception as e:
            error_details = traceback.format_exc()
            print(f"Error in show_addresses: {e}\n{error_details}")
            self.app.send_message(self.chat_id, "خطایی در نمایش آدرس‌ها رخ داد")

    def handle_picked_country(self, call):
        import math
        per_page = 15
        row_size = 3
        if call.data == '_back':
            session = self.session_manager.get_user_session(call.message.chat.id, namespace="address")
            country = session['selected_country']
        else:
            country = call.data.split("_")[-1]
        data = self.session_manager.get_user_session(call.message.chat.id, namespace="address")
        print(self.session_manager.get_user_session(call.message.chat.id, namespace="address"))
        data["state"] = "address_selection_province"
        data["selected_country"] = f"{country}"
        self.session_manager.set_user_session(call.message.chat.id, data, namespace="address")

        try:

            items = [item for item in get_province_choices(country, self.profile.lang)]
            items_name = [item[1] for item in get_province_choices(country, self.profile.lang)]
            items_code = [item[0] for item in get_province_choices(country, self.profile.lang)]
            handlers = {"prev": self.handle_prev, "next": self.handle_next}
            buttons = {}
            text = 'ساکن کدام استان هستید؟'

            if len(items)>per_page:
                paginator = InlineKeyboardPaginator(user_id=self.user_id, items=items_name, per_page=per_page, row_size=row_size, remember_last_page=True)
                buttons, layout = paginator.get_buttons_for_sendmarkup()
                
                for code, province in items:
                    if province in buttons:
                        buttons[province]["callback_data"] = f"province_{code}"
                    handlers[f'province_{code}'] = self.handle_picked_province


            else:
                counter = 0
                for code, province in items:
                    counter +=1
                    buttons[f"{province}"] = {"callback_data": f"province_{code}", "index": counter}
                    handlers[f'province_{code}'] = lambda c: self.handle_picked_province(c)
                layout = [row_size for i in range(math.floor(len(items)/row_size))]
                if len(items)%row_size:
                    for i in range(len(items)%row_size):
                        layout.append(len(items)%row_size)


            buttons['🔙'] = {'callback_data': '_back', 'index': len(buttons)+1}
            handlers["_back"] = self.handle_previous

            buttons['❌ بستن'] = {'callback_data': 'address_close', 'index': len(buttons)+2}
            handlers["address_close"] = self.handle_close
            layout.append(2)


            markup = SendMarkup(
                bot=self.app,
                chat_id=self.chat_id,
                text=text,
                buttons=buttons,
                button_layout=layout,
                handlers=handlers
            )


            markup.edit(call.message.message_id)

        except Exception as e:
            error_details = traceback.format_exc()
            print(f"Error in show_addresses: {e}\n{error_details}")
            self.app.send_message(self.chat_id, "خطایی در نمایش آدرس‌ها رخ داد")
  


    def handle_picked_province(self, call):
        per_page = 15
        row_size = 3
        province = call.data.split("_")[-1]
        data = self.session_manager.get_user_session(call.message.chat.id, namespace="address")

        data["state"] = "address_selection_city"
        data["selected_province"] = f"{province}"

        self.session_manager.set_user_session(call.message.chat.id, data, namespace="address")


        try:

            items = [item for item in get_city_choices(data["selected_country"], province, self.profile.lang)]
            items_name = [item[1] for item in get_city_choices(data["selected_country"], province, self.profile.lang)]
            items_code = [item[0] for item in get_city_choices(data["selected_country"], province, self.profile.lang)]
            handlers = {"prev": self.handle_prev, "next": self.handle_next}
            buttons = {}
            text = "ساکن کدام شهر هستید؟"

            if len(items)>per_page:
                paginator = InlineKeyboardPaginator(user_id=self.user_id, items=items_name, per_page=per_page, row_size=row_size, remember_last_page=True)
                buttons, layout = paginator.get_buttons_for_sendmarkup()
                
                for code, city in items:
                    if city in buttons:
                        buttons[city]["callback_data"] = f"city_{code}"
                    handlers[f'city_{code}'] = self.handle_picked_city


            else:
                counter = 0
                for code, city in items:
                    counter +=1
                    buttons[f"{city}"] = {"callback_data": f"city_{code}", "index": counter}
                    handlers[f'city_{code}'] = self.handle_picked_city
                layout = [row_size for i in range(math.floor(len(items)/row_size))]
                if len(items)%row_size:
                    for i in range(len(items)%row_size):
                        layout.append(len(items)%row_size)

            buttons['🔙'] = {'callback_data': '_back', 'index': len(buttons)+1}
            handlers["_back"] = self.handle_previous

            buttons['❌ بستن'] = {'callback_data': 'address_close', 'index': len(buttons)+2}
            handlers["address_close"] = self.handle_close
            layout.append(2)


            markup = SendMarkup(
                bot=self.app,
                chat_id=self.chat_id,
                text=text,
                buttons=buttons,
                button_layout=layout,
                handlers=handlers
            )



            markup.edit(call.message.message_id)
            data = self.session_manager.get_user_session(call.message.chat.id, namespace="address")
            print(data)

        except Exception as e:
            error_details = traceback.format_exc()
            print(f"Error in show_addresses: {e}\n{error_details}")
            self.app.send_message(self.chat_id, "خطایی در نمایش آدرس‌ها رخ داد")


    def handle_picked_city(self, call):

        data = self.session_manager.get_user_session(call.message.chat.id, namespace="address")

        city = call.data.split("_")[-1]

        data["state"] = "address_selection_street"
        data["selected_city"] = f"{city}"
        data["old_message"] = call.message.message_id

        self.session_manager.set_user_session(call.message.chat.id, data, namespace="address")


        text = "جزییات آدرس خود را وارد کنید. (خیابان، کوچه، پلاک)"

        markup = SendMarkup(
                bot=self.app,
                chat_id=self.chat_id,
                text=text,
                buttons=None,
                button_layout=None,
                handlers=None
            )


        markup.edit(call.message.message_id) 
        data = self.session_manager.get_user_session(call.message.chat.id, namespace="address")
        print(data)



        

    def handle_picked_street(self, message):
        data = self.session_manager.get_user_session(message.chat.id, namespace="address")

        data["state"] = "address_selection_zipcode"
        data["selected_address_line1"] = f"{message.text}"

        self.session_manager.set_user_session(message.chat.id, data, namespace="address")

        text = "لطفا کد پستی آدرس خود را وارد کنید"
        
        self.app.delete_message(message.chat.id, message.message_id)
        self.app.delete_message(message.chat.id, data["old_message"])

        message = self.app.send_message(self.chat_id, text)

        data["old_message"] = message.message_id

        self.session_manager.set_user_session(message.chat.id, data, namespace="address")


    def handle_picked_zipcode(self, message):
        try:
            data = self.session_manager.get_user_session(message.chat.id, namespace="address")

            # change postal of address previously created
            if (type(data.get("change_postal")) == list) and (data.get("change_postal")[0]):

                address = Address.objects.get(id=data.get("change_postal")[1])
                address.shipping_zip_code = int(message.text)
                address.save()

            else:
                print('ya')
                data["state"] = "address_selection_zipcode"
                data["selected_zipcode"] = f"{message.text}"

                self.session_manager.set_user_session(message.chat.id, data, namespace="address")
            
                data = self.session_manager.get_user_session(message.chat.id, namespace="address")
                if "change_address" in list(data.keys()) and data['change_address'][0]:
                    address = Address.objects.get(id=data['change_address'][1])
                    address.shipping_line1 = data["selected_address_line1"]
                    address.shipping_country=data["selected_country"]
                    address.shipping_province=data["selected_province"]
                    address.shipping_city=data["selected_city"]
                    address.shipping_zip_code=data["selected_zipcode"]
                    address.save()
                    self.app.delete_message(message.chat.id, message.message_id)
                    self.app.delete_message(message.chat.id, data["old_message"])
                else:
                    address = Address.objects.create(profile=self.profile, shipping_line1=data["selected_address_line1"], shipping_country=data["selected_country"], shipping_province=data["selected_province"], shipping_city=data["selected_city"], shipping_zip_code=data["selected_zipcode"], shipping_is_active=True) 
                    address.save()
                    self.app.delete_message(message.chat.id, message.message_id)
                    self.app.delete_message(message.chat.id, data["old_message"])

            if (type(data.get("change_postal")) == list) and (data.get("change_postal")[0]):
                self.show_single_address(address=address)
                data['change_postal'] = None
                self.session_manager.set_user_session(message.chat.id, data, namespace="address")   
                return
            if not data.get('from my postal address'):
                SendCart(self.app, self.message).invoice(self.message)
            else:
                self.show_addresses()
            self.session_manager.reset_user_session(message.chat.id, namespace="address")

        except Exception as e:
            error_details = traceback.format_exc()
            print(f"Error in show_addresses: {e}\n{error_details}")
            self.app.send_message(self.chat_id, "خطایی در نمایش آدرس‌ها رخ داد")


    def select_address(self, call, address):
        try:
            self.app.answer_callback_query(call.id, "این آدرس به عنوان آدرس فعال انتخاب شد.", show_alert=True)
            address.shipping_is_active = True
            address.save()
        except Exception as e:
            print(e)


    def change_postal(self, call):
        try:
            
            pass
        except Exception as e:
            print(f"Error in change_postal: {e}")


    def handle_previous(self, call):
        pass


    def send_location_add_address(self):
        pass



class SendPhone:
    def __init__(self, app, message_or_call):
        """
        مقداردهی اولیه کلاس
        :param app: شیء بات
        :param message_or_call: می‌تواند Message یا CallbackQuery باشد
        """
        try:
            self.app = app
            self.session_manager = session_manager
            self.user_id = (message_or_call.from_user.id if hasattr(message_or_call, 'from_user') else message_or_call.message.from_user.id)
            self.chat_id = message_or_call.chat.id if hasattr(message_or_call, 'chat') else message_or_call.message.chat.id
            self.message = message_or_call if isinstance(message_or_call, types.Message) else message_or_call.message
            self.profile = ProfileModel.objects.get(tel_id=self.chat_id)
            self.user_phone = self.profile.phone
        except Exception as e:
            error_details = traceback.format_exc()
            custom_message = f"Error in SendPhone init: {e}\nDetails:\n{error_details}"
            print(custom_message)
            self.app.send_message(self.chat_id, "خطایی در دریافت اطلاعات تماس رخ داد")

    def take_phone(self, call):
        try:
            text = "لطفا شماره تماس خود را وارد کنید. \n\n"
            text += "مثال: 09123456789"

            markup = SendMarkup(
                bot=self.app,
                chat_id=self.chat_id,
                text=text,
                buttons=None,
                button_layout=None,
                handlers=None
            )

            data = {"state": "take_phone", "old_message": call.message.message_id}
            self.session_manager.set_user_session(call.message.chat.id, data, namespace="phone")



            # ارسال یا ویرایش پیام
            if call:
                markup.edit(call.message.message_id)  # ویرایش پیام موجود
            else:
                markup.send()  # ارسال پیام جدید


        except Exception as e:
            error_details = traceback.format_exc()
            print(f"Error in show_addresses: {e}\n{error_details}")
            self.app.send_message(self.chat_id, "خطایی در گرفتن شماره تماس تابع اول‌ها رخ داد")


    def really_take_phone(self, message):
        try:
            print(message.text)
            data = self.session_manager.get_user_session(message.chat.id, namespace="phone")
            self.app.delete_message(self.chat_id, message.message_id)
            self.app.delete_message(self.chat_id, data["old_message"])

            num = int(message.text)
            self.profile.phone = num
            self.profile.save()
            SendCart(self.app, self.message).invoice(self.message)
            self.session_manager.reset_user_session(message.chat.id, namespace="phone")


        except Exception as e:
            error_details = traceback.format_exc()
            print(f"Error in show_addresses: {e}\n{error_details}")
            self.app.send_message(self.chat_id, "خطایی در گرفتن شماره تماس تابع دوم‌ها رخ داد")


