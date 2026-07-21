#./telbot/views.py
# General imports
from math import prod
import re
import trace
from traceback import format_exc, print_exception, print_tb
from tailwind import build
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
import pycountry
from django.conf import settings
from webcolors import names
from AI.settings import SITE_DOMAIN

# support imports
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import MemoryHandlerBackend, State, StatesGroup
from telebot import custom_filters

# Variables imports
from utils.balebot.helpers import get_profile
from utils.variables.TOKEN import BOT_ID
from utils.variables.TOKEN import TOKEN
from utils.variables.CHANNELS import my_channels_with_atsign, my_channels_without_atsign
from utils.telbot.functions import *
from utils.telbot.functions import UltraVideoPrompter, ProductHandler, SendCart, SendLocation, SendMarkup, t, AdvancedProductExporter
from utils.telbot.variables import customer_main_menu, extra_buttons, retun_menue, seller_main_menu, home_menu
from bs4 import BeautifulSoup

# import models
from products.models import Category, Product, ProductAttribute
from payment.models import Transaction
from telbot.models import ConversationModel, MessageModel
from telebot.types import Message
from subscription.gaurds import subscription_required


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
import telebot
from telebot import apihelper
from AI import settings



apihelper.CONNECT_TIMEOUT = 300
apihelper.READ_TIMEOUT = 600



if settings.is_proxied:
    if settings.manual_proxy:
        session = requests.Session()
        apihelper.API_URL = (
            "http://127.0.0.1:8085/api.telegram.org/bot{0}/{1}"
        )
        session.verify = False
        apihelper.session = session
    elif settings.FlaskBridge:
        apihelper.API_URL = "https://intellium.ir/bot{0}/{1}"
    else:
        
        apihelper.proxy = {
            'http': 'http://127.0.0.1:1080',
            'https': 'http://127.0.0.1:1080'
        }
        
        session = requests.Session()
        session.proxies = {
            'http': 'http://127.0.0.1:1080',
            'https': 'http://127.0.0.1:1080'
        }
        apihelper.session = session


else:
    pass





app = telebot.TeleBot(
    TOKEN,
    state_storage=state_storage,
    threaded=True,
    num_threads=5
)

app.timeout = 300





















current_site = SITE_DOMAIN

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
        if len(parts) != 6:  # باید بشه: /start store {store_id} product {product_id}
            app.send_message(message.chat.id, "لینک خرید معتبر نیست.")
            return

        _, store_id, _, product_id, _, lang = parts  # /start store_5_product_12

        

        # ست کردن فروشگاه جاری
        profile = ProfileModel.objects.get(tel_id=message.from_user.id)
        profile.server_store = Store.objects.get(id=store_id)
        profile.seller_mode = False
        profile.save()

        start(message)

        product = Product.objects.get(code=product_id)
        attributes = product.attributes.all()
        product_handler = ProductHandler(app, Product.objects.get(code=product_id), current_site, attributes=attributes, chat_id=message.chat.id)
        product_handler.send_product_message(message.chat.id)

    except Product.DoesNotExist:
        print(traceback.format_exc())
        app.send_message(message.chat.id, t(message, "item_not_available"))
    except Exception as e:
        print(traceback.format_exc())
        app.send_message(message.chat.id, f"⚠ خطا در پردازش لینک خرید: {e}")


#################################


# هندلر برای دکمه رد کردن
@app.callback_query_handler(func=lambda call: call.data and call.data.startswith("skip_video|"))
def on_skip_callback(call):
    # انتظار فرمت skip_video|<command>
    data = call.data or ""
    try:
        _prefix, command = data.split("|", 1)
    except ValueError:
        return app.answer_callback_query(call.id, "داده نامعتبر")  # ← از app استفاده کن

    user_id = call.from_user.id
    try:
        profile = ProfileModel.objects.get(tel_id=user_id)
    except ProfileModel.DoesNotExist:
        return app.answer_callback_query(call.id, "پروفایل یافت نشد")  # ← از app استفاده کن

    # hide for all languages
    try:
        profile.hide_video(command)
        # اصلاح: از app استفاده کن نه call.bot
        app.edit_message_reply_markup(
            chat_id=call.message.chat.id, 
            message_id=call.message.message_id, 
            reply_markup=None
        )
        app.answer_callback_query(call.id, "✅ دیگر این ویدیو برای شما نمایش داده نخواهد شد", show_alert=True)
    except Exception as e:
        logger.exception("hide_video failed")
        app.answer_callback_query(call.id, "خطا در ثبت درخواست", show_alert=True)




# Start handler
@app.message_handler(commands=['start'])
def start(message):
    try:
        tel_id = message.from_user.id
        print(f"chat id: {message.chat.id}")
        print(f"from user id: {message.from_user.id}")
        tel_username = message.from_user.username
        tel_first_name = message.from_user.first_name
        tel_last_name = message.from_user.last_name


        # Prepare the signed request
        payload = {"tel_id": tel_id}

        # Create the signed headers
        body_str = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
        body = body_str.encode("utf-8")
        ts, sig = sign_payload(BOT_SECRET, body)
        nonce = str(uuid.uuid4())

        headers = {
            "X-Bot-Timestamp": ts,
            "X-Bot-Signature": sig,
            "X-Bot-Nonce": nonce,
            "Content-Type": "application/json",
        }

        # Send signed request
        response = requests.post(
            f"{current_site}/telbot/api/check-registration/",
            headers=headers,
            data=body  # Use data, not json, to maintain exact body for signature
        )

        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")

        
        profile, created = ProfileModel.objects.get_or_create(
            tel_id=tel_id,
            telegram=tel_username,
            fname=tel_first_name,
            lname=tel_last_name
        )

        if created:
            language_setting(message)
        else:
            home(message)

    except Exception as e:
        app.send_message(message.chat.id, t(message, "start_error"))
        print(traceback.format_exc())


#####################################################################################################




# from ai_chat.views import QwenOllamaClient
# import traceback
# import time
# from threading import Thread, Lock
# import asyncio
# from queue import Queue
# from typing import Dict, List, Optional, Union, Iterator  # این خط را اضافه کنید

# import traceback
# import time
# import json
# from threading import Thread, Lock
# from queue import Queue
# from typing import Dict, List, Optional, Union, Iterator

# from ai_chat.views import QwenOllamaClient

# # ایجاد کلاینت گلوبال - ابتدا تست می‌کنیم کدام مدل کار می‌کند
# def init_qwen_client():
#     """ایجاد کلاینت با تست اتصال"""
#     models_to_try = [
#         "qwen2.5:0.5b",    # سبک‌ترین
#         "qwen2.5:1.5b",    # متوسط
#         "my-qwen:latest",  # custom 7B
#         "qwen2.5:7b"       # استاندارد 7B
#     ]
    
#     for model in models_to_try:
#         try:
#             client = QwenOllamaClient(
#                 default_model=model,
#                 timeout=120
#             )
            
#             # تست اتصال
#             print(f"🔍 تست مدل: {model}")
#             models = client.list_models()
#             if models:
#                 print(f"✅ مدل {model} کار می‌کند")
#                 return client
                
#         except Exception as e:
#             print(f"❌ مدل {model} خطا: {e}")
#             continue
    
#     # اگر هیچ کدام کار نکرد، حداقل یک کلاینت ایجاد کن
#     print("⚠️ هیچ مدلی کار نکرد، ایجاد کلاینت با تنظیمات پیش‌فرض")
#     return QwenOllamaClient(default_model="qwen2.5:0.5b", timeout=120)

# # ایجاد کلاینت
# qwen_client = init_qwen_client()
# print(f"🎯 مدل انتخاب شده: {qwen_client.default_model}")

# # دیکشنری برای ذخیره وضعیت استریم هر کاربر
# user_stream_status = {}
# stream_locks = {}

# class TelegramStreamHandler:
#     """مدیریت استریم پاسخ برای تلگرام"""

#     def __init__(self, chat_id, app):
#         self.chat_id = chat_id
#         self.app = app
#         self.response_text = ""
#         self.message_id = None
#         self.is_streaming = True
#         self.last_update_time = time.time()

#     def update_message(self, text_chunk):
#         """آپدیت پیام تلگرام با متن جدید"""
#         try:
#             if not self.message_id:
#                 # ارسال اولین پیام
#                 msg = self.app.send_message(self.chat_id, text_chunk[:200] + "..." if len(text_chunk) > 200 else text_chunk)
#                 self.message_id = msg.message_id
#             else:
#                 # آپدیت پیام موجود
#                 if len(text_chunk) > 4000:
#                     text_chunk = text_chunk[:4000] + "..."
#                 self.app.edit_message_text(
#                     text_chunk,
#                     chat_id=self.chat_id,
#                     message_id=self.message_id
#                 )
#             self.last_update_time = time.time()
#             return True
#         except Exception as e:
#             print(f"⚠️ خطا در آپدیت پیام: {e}")
#             return False

#     def add_chunk(self, chunk):
#         """اضافه کردن بخش جدید به پاسخ"""
#         if chunk:
#             self.response_text += chunk
            
#             # آپدیت پیام هر 0.5 ثانیه یا اگر متن قابل توجهی اضافه شده
#             current_time = time.time()
#             if current_time - self.last_update_time >= 0.5 or len(chunk) > 30:
#                 return self.update_message(self.response_text)
#         return True

#     def finalize(self):
#         """پایان استریم"""
#         self.is_streaming = False
#         # آپدیت نهایی
#         if len(self.response_text) > 4000:
#             self.response_text = self.response_text[:4000] + "..."
#         if self.message_id:
#             try:
#                 self.app.edit_message_text(
#                     self.response_text,
#                     chat_id=self.chat_id,
#                     message_id=self.message_id
#                 )
#             except Exception as e:
#                 print(f"⚠️ خطا در آپدیت نهایی: {e}")
#                 # اگر آپدیت نشد، پیام جدید بفرست
#                 try:
#                     self.app.send_message(self.chat_id, self.response_text)
#                 except:
#                     pass
#         return self.response_text

# def create_prompt_for_story(user_input):
#     """ایجاد پرامپت مخصوص داستان‌نویسی"""
#     prompt = f"""تو یک نویسنده خلاق فارسی‌زبان هستی. کاربر این درخواست را دارد: "{user_input}"

# یک داستان کوتاه و جذاب بنویس که:
# 1. ابتدا و میانه و پایان مشخص داشته باشد
# 2. شخصیت‌های جذاب داشته باشد
# 3. توصیفات زیبا و تصویرسازی قوی داشته باشد
# 4. پیام اخلاقی یا نکته آموزنده داشته باشد
# 5. کاملاً به زبان فارسی و روان نوشته شود
# 6. حدود 200-300 کلمه باشد

# داستان:"""
#     return prompt

# def create_general_prompt(user_input):
#     """ایجاد پرامپت برای سوالات عمومی"""
#     prompt = f"""تو یک دستیار هوشمند، مفید و دوستانه فارسی‌زبان هستی.

# سوال کاربر: {user_input}

# لطفاً پاسخ خود را با این ویژگی‌ها بده:
# - کاملاً به فارسی
# - طبیعی و انسانی
# - مفید و دقیق
# - دوستانه و محترمانه
# - اگر اطلاعات کافی نداری، صادقانه بگو

# پاسخ:"""
#     return prompt

# def handle_stream_response(chat_id, text):
#     """مدیریت پاسخ استریمی"""
#     stream_handler = None

#     try:
#         # نمایش وضعیت "در حال تایپ"
#         app.send_chat_action(chat_id, 'typing')

#         # ایجاد هندلر
#         stream_handler = TelegramStreamHandler(chat_id, app)
#         user_stream_status[chat_id] = stream_handler

#         print(f"📨 User ({chat_id}): {text}")

#         # تشخیص نوع سوال و انتخاب پرامپت مناسب
#         if any(keyword in text.lower() for keyword in ['داستان', 'قصه', 'روایت', 'ماجرا']):
#             optimized_prompt = create_prompt_for_story(text)
#             max_tokens = 1000  # برای داستان بیشتر
#         else:
#             optimized_prompt = create_general_prompt(text)
#             max_tokens = 800

#         # تنظیمات بهینه
#         stream_options = {
#             "temperature": 0.8,        # برای خلاقیت بیشتر
#             "top_p": 0.9,
#             "top_k": 50,
#             "num_predict": max_tokens,
#             "repeat_penalty": 1.1,
#             "num_ctx": 2048,
#             "seed": int(time.time()) % 1000  # seed تصادفی
#         }

#         # زمان‌سنجی
#         start_time = time.time()

#         # دریافت استریم پاسخ - استفاده از simple_generate_stream
#         try:
#             # اول سعی کن با stream
#             for chunk in qwen_client.generate(
#                 prompt=optimized_prompt,
#                 model=qwen_client.default_model,
#                 options=stream_options,
#                 stream=True
#             ):
#                 if not stream_handler.is_streaming:
#                     break

#                 if chunk:
#                     success = stream_handler.add_chunk(chunk)
#                     if not success:
#                         break
                        
#         except Exception as stream_error:
#             print(f"⚠️ خطا در استریم، استفاده از روش مستقیم: {stream_error}")
#             # اگر استریم کار نکرد، از روش مستقیم استفاده کن
#             direct_response = get_direct_response(text, optimized_prompt)
#             if direct_response:
#                 stream_handler.response_text = direct_response
#                 stream_handler.update_message(direct_response)

#         # پایان استریم
#         if stream_handler:
#             final_response = stream_handler.finalize()
#             elapsed_time = time.time() - start_time
#             print(f"✅ Bot ({chat_id}): پاسخ در {elapsed_time:.1f} ثانیه")

#     except Exception as e:
#         error_msg = f"خطا: {str(e)[:100]}"
#         print(f"❌ خطا در handle_stream_response: {error_msg}")

#         try:
#             # تلاش برای ارسال پیام خطا
#             if stream_handler and stream_handler.message_id:
#                 app.edit_message_text(
#                     f"⚠️ خطا در پردازش: {error_msg}",
#                     chat_id=chat_id,
#                     message_id=stream_handler.message_id
#                 )
#             else:
#                 app.send_message(chat_id, f"⚠️ خطا در پردازش درخواست")
#         except:
#             try:
#                 app.send_message(chat_id, "⚠️ مشکل فنی رخ داده است")
#             except:
#                 pass

#     finally:
#         # پاک‌سازی
#         if chat_id in user_stream_status:
#             del user_stream_status[chat_id]

#         # غیرفعال کردن حالت چت
#         try:
#             session = session_manager.get_user_session(chat_id, namespace="AIchat")
#             session["chat"] = False
#             session_manager.set_user_session(chat_id, session, namespace="AIchat")
#         except:
#             pass

# def get_direct_response(question, prompt=None):
#     """دریافت پاسخ مستقیم (بدون استریم)"""
#     try:
#         if prompt is None:
#             prompt = create_general_prompt(question)
        
#         # تنظیمات برای پاسخ مستقیم
#         options = {
#             "temperature": 0.7,
#             "num_predict": 600,
#             "top_p": 0.85,
#             "repeat_penalty": 1.1
#         }
        
#         # استفاده از simple_generate اگر موجود باشد
#         if hasattr(qwen_client, 'simple_generate'):
#             response = qwen_client.simple_generate(prompt, max_tokens=600)
#         else:
#             # روش جایگزین
#             response = qwen_client.generate(
#                 prompt=prompt,
#                 options=options,
#                 stream=False
#             )
#             if isinstance(response, dict):
#                 response = response.get('response', '')
        
#         return clean_response(str(response))
        
#     except Exception as e:
#         print(f"❌ خطا در get_direct_response: {e}")
#         return f"⚠️ خطا در تولید پاسخ: {str(e)[:50]}"

# def clean_response(text):
#     """پاک‌سازی پاسخ"""
#     if not text:
#         return "پاسخی دریافت نشد."
    
#     # حذف عبارات تکراری
#     lines = text.split('\n')
#     cleaned = []
    
#     for line in lines:
#         line = line.strip()
#         if not line:
#             continue
        
#         # حذف خطوط تکراری
#         if line not in cleaned:
#             cleaned.append(line)
    
#     result = '\n'.join(cleaned)
    
#     # حذف پرامپت احتمالی
#     unwanted_prefixes = ['پاسخ:', 'جواب:', 'داستان:', 'نتیجه:']
#     for prefix in unwanted_prefixes:
#         if result.startswith(prefix):
#             result = result[len(prefix):].strip()
    
#     # اگر خیلی کوتاه است
#     if len(result) < 10:
#         result = "پاسخ کوتاه: متأسفانه نتوانستم پاسخ مناسبی تولید کنم. لطفاً سوال را واضح‌تر بیان کنید."
    
#     return result

# def handle_telegram_message(chat_id, text):
#     """پردازش پیام تلگرام"""
#     chat_id_str = str(chat_id)

#     # بررسی درخواست همزمان
#     if chat_id_str in stream_locks and stream_locks[chat_id_str].locked():
#         app.send_message(chat_id, "⏳ لطفاً منتظر بمانید، در حال پردازش درخواست قبلی...")
#         return

#     # ایجاد قفل
#     if chat_id_str not in stream_locks:
#         stream_locks[chat_id_str] = Lock()

#     # اجرا در ترد جداگانه
#     def run_stream():
#         with stream_locks[chat_id_str]:
#             handle_stream_response(chat_id, text)

#     thread = Thread(target=run_stream, daemon=True)
#     thread.start()

# def send_quick_response(chat_id, text):
#     """ارسال پاسخ سریع (بدون استریم)"""
#     try:
#         # ارسال پیام در حال پردازش
#         msg = app.send_message(chat_id, "🔄 در حال پردازش...")
        
#         # دریافت پاسخ
#         response = get_direct_response(text)
        
#         # آپدیت پیام
#         app.edit_message_text(
#             response,
#             chat_id=chat_id,
#             message_id=msg.message_id
#         )
        
#     except Exception as e:
#         app.send_message(chat_id, f"⚠️ خطا: {str(e)[:100]}")
#     finally:
#         # غیرفعال کردن حالت چت
#         try:
#             session = session_manager.get_user_session(chat_id, namespace="AIchat")
#             session["chat"] = False
#             session_manager.set_user_session(chat_id, session, namespace="AIchat")
#         except:
#             pass

# @app.message_handler(func=lambda message: message.text == "AI")
# def chat_with_me(message):
#     """شروع مکالمه"""
#     try:
#         # متوقف کردن استریم قبلی
#         if message.chat.id in user_stream_status:
#             user_stream_status[message.chat.id].is_streaming = False
#             time.sleep(0.5)

#         # فعال کردن حالت چت
#         session_manager.set_user_session(
#             message.chat.id,
#             {"chat": True},
#             namespace="AIchat"
#         )

#         welcome_msg = f"""🤖 *دستیار هوشمند فعال شد*

# • مدل: {qwen_client.default_model}
# • پاسخ‌دهی فارسی روان
# • پشتیبانی از داستان‌نویسی
# • پردازش هوشمند

# سوال یا درخواست خود را مطرح کنید..."""

#         app.send_message(message.chat.id, welcome_msg, parse_mode='Markdown')

#     except Exception as e:
#         print(f"❌ خطا در شروع چت: {e}")
#         app.send_message(message.chat.id, "✨ آماده پاسخگویی!")

# @app.message_handler(func=lambda message: session_manager.get_user_session(message.chat.id, namespace="AIchat").get("chat"))
# def responseme(message):
#     """پاسخ به پیام کاربر"""
#     try:
#         text = message.text.strip()
#         if not text:
#             return

#         # دستورات مدیریتی
#         if text.lower() in ['/stop', 'توقف', 'stop', 'بس']:
#             if message.chat.id in user_stream_status:
#                 user_stream_status[message.chat.id].is_streaming = False
#                 app.send_message(message.chat.id, "⏹️ متوقف شد")
#             return

#         if text.lower() in ['/fast', 'سریع']:
#             # استفاده از پاسخ سریع
#             send_quick_response(message.chat.id, text)
#             return

#         # برای سوالات کوتاه از پاسخ سریع، برای داستان و طولانی‌تر از استریم
#         if len(text) < 50 and not any(keyword in text.lower() for keyword in ['داستان', 'قصه', 'توضیح', 'شرح']):
#             send_quick_response(message.chat.id, text)
#         else:
#             handle_telegram_message(message.chat.id, text)

#     except Exception as e:
#         print(f"❌ خطا در responseme: {e}")
#         app.send_message(message.chat.id, "⚠️ خطای موقت، لطفاً دوباره تلاش کنید")

# # دستور برای تست API
# @app.message_handler(commands=['test_ai'])
# def test_ai_command(message):
#     """تست اتصال AI"""
#     try:
#         app.send_message(message.chat.id, "🔍 در حال تست اتصال به AI...")
        
#         # تست ساده
#         test_response = get_direct_response("سلام، حالت چطوره؟")
        
#         if "خطا" in test_response:
#             app.send_message(message.chat.id, f"❌ تست ناموفق: {test_response}")
#         else:
#             app.send_message(message.chat.id, f"✅ تست موفق!\nمدل: {qwen_client.default_model}\n\nپاسخ تست: {test_response[:200]}...")
            
#     except Exception as e:
#         app.send_message(message.chat.id, f"❌ خطا در تست: {e}")






#####################################################################################################

# HOME
@app.message_handler(func=lambda message: message.text == "🏡")
def home(message, text=None, *args, **kwargs):
    try:
        if isinstance(message, types.Message):
            message = message
            call_data = None
            is_callback = False
            id = message.chat.id
        else:
            message = message.message
            is_callback = True
            id = message.chat.id
    except Exception as e:
        error_details = traceback.format_exc()
        custom_message = f"An error occurred: {e}\nDetails:\n{error_details}"
        print(f"{custom_message}")

    if subscription.subscription_offer(message):
        session_manager.unlock(message.chat.id)
        session_list = ["address", "menu", "add_product", "delete_product", "phone", "createshop", "variants"]
        if kwargs.get("session_delete"): # session_delete must be a tuple
            for i in session_list:
                if i in kwargs.get("session_delete"):
                    continue
                session_manager.reset_user_session(message.chat.id, namespace=i)
        else:
            for i in session_list:
                session_manager.reset_user_session(message.chat.id, namespace=i)

        profile = ProfileModel.objects.get(tel_id=id)
        markup = send_menu(message, profile.tel_menu, "main_menu", profile.extra_button_menu)
        if not text:
            text = t(message, "home_message")
        return app.send_message(message.chat.id, text, reply_markup=markup)


# Visit website
# @app.message_handler(func=lambda message: message.text == t(message, "visit_website"))
# def visit_website(message):
#     if subscription.subscription_offer(message):
#         send_website_link(message)



# settings handler
@app.message_handler(func=lambda message: message.text == t(message, "menu_settings"))
def settings(message):
    if subscription.subscription_offer(message):
        home_menue = ["🏡"]
        ##############################
        #attention you can do so
        #from utils.telbot.variables import home_menu
        ##############################
        markup = send_menu(message, ProfileModel.objects.get(tel_id=message.chat.id).settings_menu, "settings",
                           home_menue, 2)
        app.send_message(message.chat.id, t(message, "settings_message"), reply_markup=markup)


@app.message_handler(func=lambda message: message.text == t(message, "menu_create_shop"))
def menu_create_shop(message):
    try:
        build_shop(message)
    except:
        print(traceback.format_exc())


# profile settings handler
@app.message_handler(func=lambda message: message.text in (translations["menu_profile"][ProfileModel.objects.get(tel_id=message.chat.id).lang]))
def profile_setting(message):
    if subscription.subscription_offer(message):
        home_menue = ["🏡"]
        ##############################
        #attention you can do so
        #from utils.telbot.variables import home_menu
        ##############################
        markup = send_menu(message, ProfileModel.objects.get(tel_id=message.from_user.id).profile_menu, "profile",
                           home_menue)
        app.send_message(message.chat.id, t(message, "profile_settings"), reply_markup=markup)


@app.message_handler(func=lambda message: message.text == t(message, "currency_settings"))
def currency_setting(message):
    # try:
    #     if subscription.subscription_offer(message):
    #         from utils.telbot.variables import home_menu
    #         profile = ProfileModel.objects.get(tel_id=message.chat.id)
    #         text = t(message, "currency_setting_description", current_currency=str(profile.preferred_currency))
    #         if Store.objects.filter(owner=profile).exists():
    #             text += "\n\n" + t(message, "currency_setting_warning")
    #         currancies = [name.split(" - ")[1] for code, name in ProfileModel.get_currency_choices()]
    #         paginator = InlineKeyboardPaginator(user_id=message.chat.id, items=currancies, per_page=24, row_size=3, remember_last_page=False)
    #         buttons, layout = paginator.get_buttons_for_sendmarkup()

    #         handlers = {"prev": lambda a: None, "next": lambda b: None}  # Define handlers for prev and next buttons if needed
    #         currancies = [curr for curr in ProfileModel.get_currency_choices()]
    #         for code, name in currancies:
    #             if name in buttons:
    #                 name = name.split(" - ")[1]
    #                 buttons[name]["callback_data"] = f"currncy_{code}"
    #                 handlers[f'currency_{code}'] = lambda a: None
            
    #         buttons[t(message, "close")] = {'callback_data': 'currency_close', 'index': len(buttons)+2}
    #         handlers["currency_close"] = lambda a: None
    #         layout.append(1)

    #         data = session_manager.get_user_session(message.chat.id, namespace="currency")
    #         data["state"] = "currency_selection"
    #         session_manager.set_user_session(message.chat.id, data, namespace="currency")

    #         # ایجاد کیبورد
    #         markup = SendMarkup(
    #             bot=app,
    #             chat_id=message.chat.id,
    #             text=text,
    #             buttons=buttons,
    #             button_layout=layout,
    #             handlers=handlers
    #         )
    #         markup.send()
    pass
    # except Exception as e:
    #     error_details = traceback.format_exc()
    #     print(f"Error in currency_setting: {e}\nDetails:\n{error_details}")


@app.message_handler(func=lambda message: message.text == t(message, "menu_store"))
def store_setting(message):
    if subscription.subscription_offer(message):
        session = session_manager.get_user_session(message.chat.id, namespace="menu")
        session["store_lang"] = True
        home_menue = ["🏡"]
        ##############################
        #attention you can do so
        #from utils.telbot.variables import home_menu
        ##############################
        markup = send_menu(message, ProfileModel.objects.get(tel_id=message.from_user.id).store_menu, "store",
                           home_menue)
        app.send_message(message.chat.id, t(message, "store_settings"), reply_markup=markup)
        session_manager.set_user_session(message.chat.id, session, namespace="menu")



# balance
@app.message_handler(func=lambda message: message.text == translations["menu_wallet"][ProfileModel.objects.get(tel_id=message.chat.id).lang])
def balance_menue(message):
    if subscription.subscription_offer(message):
        profile = ProfileModel.objects.get(tel_id=message.chat.id)
        options = [t(message, "my_balance"), t(message, "increase_balance")]
        if Store.objects.filter(owner=profile).first():
            options.append(t(message, "withdraw"))
        home_menue = ["🏡"]
        ##############################
        #attention you can do so
        #from utils.telbot.variables import home_menu
        ##############################
        markup = send_menu(message, options, "balance_category", home_menue, cols=2)
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
            profile = ProfileModel.objects.get(tel_id=message.chat.id)
            store = Store.objects.get(owner=ProfileModel.objects.get(tel_id=message.chat.id))
            # if store.status:
            profile.seller_mode = True
            # else:
                # promotion(message)
                # return
            profile.settings_menu = profile.LEVEL_MENUS["seller"][2]
            profile.save()
            profile.save()
            markup = send_menu(message, profile.tel_menu, "settings", profile.extra_button_menu)
            app.send_message(message.chat.id, t(message, "become_a_seller"), reply_markup=markup)
        except Store.DoesNotExist:
            app.send_message(message.chat.id, t(message, "become_a_seller_no_store"))
        except:
            print(traceback.format_exc())


# back to buyer mode handler# become a seller handler
@app.message_handler(func=lambda message: message.text in (translations["menu_back_to_buyer"][ProfileModel.objects.get(tel_id=message.chat.id).lang]))
def back_to_buyer(message, text=None, *args, **kwargs):
    if subscription.subscription_offer(message):
        profile = ProfileModel.objects.get(tel_id=message.chat.id)
        profile.seller_mode = False
        profile.settings_menu = profile.LEVEL_MENUS[profile.user_level][2]
        profile.save()
        profile.save()

        home(message, text=text)


from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,    
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
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
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from django.core.cache import cache
import tempfile
import gc
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
import re
from datetime import datetime

def safe_filename(text: str) -> str:
    """
    حذف کاراکترهای غیرمجاز برای نام فایل
    """
    text = re.sub(r'[\\/*?:"<>|]', '', text)
    return text.strip().replace(" ", "_")


def rtl(text: str) -> str:
    return get_display(arabic_reshaper.reshape(str(text)))


def generate_sales_pdf(store, sales_data, font_path, chat_id):
    # ---------- filename ----------
    today = datetime.now().strftime("%Y-%m-%d")
    store_name = safe_filename(store.name)
    filename = f"{store_name}_{today}.pdf"

    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, filename)

    # ---------- font ----------
    if "Vazir" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("Vazir", font_path))

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=24,
        leftMargin=24,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="RTLTitle",
        fontName="Vazir",
        fontSize=14,
        alignment=TA_CENTER,
        spaceAfter=16
    ))

    elements = []

    title_text = rtl(
        t("message", "sale_statistics_title", chat_id=chat_id)
        .format(store_name=store.name)
    )
    elements.append(Paragraph(title_text, styles["RTLTitle"]))
    elements.append(Spacer(1, 12))

    headers = [
        rtl(t("message", "sale_statistics_index", chat_id=chat_id)),
        rtl(t("message", "sale_statistics_date", chat_id=chat_id)),
        rtl(t("message", "sale_statistics_quantity", chat_id=chat_id)),
        rtl(t("message", "sale_statistics_total_cost", chat_id=chat_id, currency=t("message", ProfileModel.objects.get(tel_id=chat_id).preferred_currency, chat_id=chat_id))),
        rtl(t("message", "sale_statistics_product_name", chat_id=chat_id)),
    ]

    table_data = [headers]
    total_amount = 0

    for idx, sale in enumerate(sales_data, start=1):
        total_amount += sale["total_price"]
        table_data.append([
            idx,
            rtl(sale["date"]),
            sale["quantity"],
            f"{sale['total_price']:,.0f}",
            rtl(sale["product_name"][:35]),
        ])

    table_data.append([
        "",
        "",
        "",
        f"{total_amount:,.0f}",
        rtl(t("message", "sale_statistics_total", chat_id=chat_id)),
    ])

    table = Table(
        table_data,
        colWidths=[40, 75, 55, 90, 200],
        repeatRows=1
    )

    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Vazir'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
        ('SPAN', (3, -1), (4, -1)),
    ]))

    elements.append(table)
    doc.build(elements)

    return file_path





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
            from django.conf import settings
            file_path = None

            try:
                font_path = os.path.join(settings.MEDIA_ROOT, "fonts", "Vazir.ttf")

                file_path = generate_sales_pdf(
                    store=store,
                    sales_data=sales_data,
                    font_path=font_path,
                    chat_id=chat_id
                )

                with open(file_path, "rb") as f:
                    app.send_document(
                        chat_id,
                        f,
                        caption=t(message, "sale_statistics_ready")
                    )

            except Exception:
                app.send_message(chat_id, t(message, "sale_statistics_error"))
                print(traceback.format_exc())

            finally:
                # 🔥 حذف فایل از سرور
                if file_path and os.path.exists(file_path):
                    os.unlink(file_path)

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

        product_handler = ProductHandler(app, product, current_site, attributes=product.attributes.all(), chat_id=call.message.chat.id)
        
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
        product_handler = ProductHandler(app, product, current_site, attributes=product.attributes.all(), chat_id=call.message.chat.id)
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
        product_handler = ProductHandler(app, product, current_site, attributes=product.attributes.all(), chat_id=call.message.chat.id)
        product_handler.handle_comments(call)

    except ObjectDoesNotExist:
        app.answer_callback_query(call.id, "محصول یافت نشد!", show_alert=True)
    except Exception as e:
        error_message = traceback.format_exc()
        print(f"Error in handle_comments: {e}\n{error_message}")


@app.callback_query_handler(func=lambda call: call.data == "add" or call.data == "remove" or call.data == "reduce")
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
@app.callback_query_handler(func=lambda call: call.data.startswith("cart_")) # استفاده از "cart_" برای هندلرهای پویا
@app.callback_query_handler(func=lambda call: call.data == "finalize" or call.data == "view_cart")
def cart_CallBack(data):
    try:
        if isinstance(data, types.Message):
            # اگر پیام است
            message = data
            chat_id = message.chat.id
            is_callback = False
        elif isinstance(data, types.CallbackQuery):
            # اگر کال‌بک کوئری است
            message = data.message
            chat_id = message.chat.id
            is_callback = True
        else:
            return

        # 3. ایجاد شیء SendCart با آرگومان‌های صحیح
        # نکته: app (بات) به عنوان آرگومان bot، chat_id، و user_cart به عنوان cart ارسال می‌شوند.
        cart_menu = SendCart(app, message)

        if not is_callback or data.data == "view_cart" or data.data == "finalize":
            # پاسخ به دستور متنی یا درخواست‌های ارسال مجدد منو
            profile = ProfileModel.objects.get(tel_id=message.chat.id)
            cart = Cart.objects.filter(profile=profile).first()
            cart_items = cart.items.exists()
            if is_callback and (not cart or not cart_items):
#                app.send_message(message.chat.id, t(message, "cart_empty"))
                return
            cart_menu.send()
            
            # در صورتی که نیاز به مدیریت دکمه "finalize" دارید:
            if is_callback and data.data == "finalize":
                 # منطق انتقال به مرحله نهایی پرداخت (مثلاً تابع دیگری صدا زده شود)
                 print("me")
                 pass

        elif is_callback:
            # مدیریت دکمه‌های پویا در SendCart (مانند cart_toggle یا cart_inc/dec)
            # توجه: متد handle_callback در طرح SendCart تعریف شده است.
            cart_menu.handle_callback(data)
            
    except ProfileModel.DoesNotExist:
        print(f"Error: Profile not found for chat ID {data.chat.id}")
    except Exception as e:
        print(f"Error in cart_CallBack: {e}\n{traceback.format_exc()}")


        
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
                product_handler = ProductHandler(app, product, current_site, attributes=product.attributes.all(), chat_id=message.chat.id)
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
     'prev', 'country_', 'province_', 'city_', '_back', "change_address", "store_address", "add_address_store")) or call.data in ("back_to_addresses"))
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
        actions = call_data.split("_") if call_data else []
        loc = SendLocation(app, message)
        session = session_manager.get_user_session(message.chat.id, namespace="address") or {}
        
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
            session = session_manager.get_user_session(message.chat.id, namespace="address") or {}
            if session.get("show_store_address"):
                session_manager.reset_user_session(message.chat.id, namespace="address")
                app.delete_message(message.chat.id, message.message_id)
                build_shop(message)
                return
            loc.show_addresses(data)
        elif call_data.startswith("show_address_"):
            address_id = int(call_data.split("_")[-1])
            address = Address.objects.get(id=address_id)
            if actions[-2] == "store":
                session['show_store_address'] = True
                session_manager.set_user_session(message.chat.id, session, namespace="address")
            loc.show_single_address(address, call=data)
        elif call_data.startswith("address_"):
            pass# loc.show_single_address(data, address)
        
        elif call_data.startswith('close_address'):
            loc.handle_close(data)
        elif call_data.startswith('delete_address_'):
            address_id = int(call_data.split("_")[-1])
            address = Address.objects.get(id=address_id)
            loc.delete_address(data, address)
        elif call_data.startswith("add_new_address"):
            print("yes add new address")
            loc.add_new_address(data)
        elif call_data.startswith("manual_add_address") or call_data.startswith("change_address") or call_data.startswith("add_address_store"):
            if call_data.startswith("change_address"):
                address_id = int(call_data.split("_")[-1])
                session['change_address'] = (True, address_id)
                session_manager.set_user_session(message.chat.id, session, namespace="address")
            if actions[-2] == "store":
                session['add_store_address'] = True
                session['store_id'] = actions[-1]
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
        if isinstance(data, types.Message):
            app.send_message(message.chat.id, t(message, "address_not_found"))
        else:
            app.answer_callback_query(data.id, text=t(message, "address_not_found"), show_alert=False)
        if actions[-2] == "store":
            session.pop('add_store_address', None)
            session.pop('store_id', None)
            session_manager.set_user_session(message.chat.id, session, namespace="address")
            app.delete_message(data.message.chat.id, data.message.message_id)
            app.delete_message(data.message.chat.id, data.message.message_id - 1)
            build_shop(message)
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



@app.message_handler(func=lambda message: message.text == t(message, "menu_change_warehouse"))
def warehouse_location(message):
    try:
        session = session_manager.get_user_session(message.chat.id, namespace="address") or {}
        loc = SendLocation(app, message)
        profile = ProfileModel.objects.get(tel_id=message.chat.id)
        store = Store.objects.get(owner=profile)
        session["store_id"] = store.id
        address = store.get_address()
        session["store_address_message"] = True
        if address:
            session['show_store_address'] = True
            session_manager.set_user_session(message.chat.id, session, namespace="address")
            loc.show_single_address(address, call=message)
        else:
            session['add_store_address'] = True
            session_manager.set_user_session(message.chat.id, session, namespace="address")
            loc.manual_add_address(message)
        
    except:
        print(traceback.format_exc())


@app.message_handler(func=lambda message: message.text in ('🇮🇷 فارسی', '🇬🇧  English', '🇨🇳  中国人', '🇷🇺  русский', '🇵🇸  عربیة',))
def change_lang(message):
    try:
        session = session_manager.get_user_session(message.chat.id, namespace="menu")
        profile = ProfileModel.objects.get(tel_id=message.chat.id)
        if session.get("store_lang", None):
            store = Store.objects.filter(owner=profile).first()
            if 'فارسی' in message.text:
                store.lang = 'fa'
            elif 'English' in message.text:
                store.lang = 'en'
            elif "中国人" in message.text:
                store.lang = 'zh'
            elif "русский" in message.text:
                store.lang = 'ru'
            elif "عربیة" in message.text:
                store.lang = 'ar'
            store.save()
        else:
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
        text = t(message, "store_language_changed") if session.get("store_lang", None) else t(message, "your_lang_changed")
        home(message, text=text)
        
    except Exception as e:
        print(f"Error in change language handler: {e}\n{traceback.format_exc()}")


# Back to Previous Menu
@app.message_handler(func=lambda message: message.text == "🔙")
def handle_back(message):
    if not subscription.subscription_offer(message):
        return

    try:
        session = session_manager.get_user_session(
            message.chat.id,
            namespace="menu",
        )

        profile = ProfileModel.objects.get(tel_id=message.chat.id)

        if profile.seller_mode:
            store = Store.objects.get(owner=profile)
        else:
            store = profile.server_store

        current_category_id = session.get("current_category_id")

        # اگر در ریشه هستیم
        if current_category_id is None:

            if session.get("category") and session.get("menu_add"):
                session["parent_for_new"] = None
                session_manager.set_user_session(
                    message.chat.id,
                    session,
                    namespace="menu",
                )

            fake_message = message
            fake_message.text = t(message, "menu_categories")
            category_client(fake_message)
            return

        status = None if session.get("category") and session.get("category_deactivate") else True

        current_category = Category.objects.select_related("parent").get(
            pk=current_category_id,
            store=store,
            **({} if status is None else {"status": True}),
        )

        parent = current_category.parent

        # اگر دسته فعلی ریشه است
        if parent is None:

            session["current_category_id"] = None
            session["current_menu"] = None

            if session.get("category") and session.get("menu_add"):
                session["parent_for_new"] = None

            session_manager.set_user_session(
                message.chat.id,
                session,
                namespace="menu",
            )

            fake_message = message
            fake_message.text = t(message, "menu_categories")
            category_client(fake_message)
            return

        # یک سطح بالا برو
        session["current_category_id"] = parent.parent_id
        session["current_menu"] = parent.title.lower()

        if session.get("category") and session.get("menu_add"):
            session["parent_for_new"] = parent.id

        session_manager.set_user_session(
            message.chat.id,
            session,
            namespace="menu",
        )

        fake_message = message
        fake_message.text = parent.title
        subcategory(fake_message)

    except Exception:
        print(traceback.format_exc())


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
                        product_handler = ProductHandler(app, product, current_site, attributes=product.attributes.all(), chat_id=message.chat.id)
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
        profile = ProfileModel.objects.get(tel_id=message.chat.id)
        store = profile.server_store
        sup_markup = types.InlineKeyboardMarkup()
        client_markup = types.InlineKeyboardMarkup()

        sup_markup.add(types.InlineKeyboardButton(text=t(message, "reply"), callback_data="پاسخ"))
        client_markup.add(types.InlineKeyboardButton(text=t(message, "end_chat"), callback_data=t(message, "end_chat")))

        app.send_message(chat_id=store.owner.tel_id,
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
            ##############################
            #attention you can do so
            #from utils.telbot.variables import home_menu
            ##############################
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



@app.message_handler(func=lambda m: m.text == t(m, "menu_add") and
                     session_manager.get_user_session(m.chat.id, namespace="menu").get("category")
                     and session_manager.can_execute(m.chat.id))
@UltraVideoPrompter(command="menu_add")
def add_category_handler(message):
    try:
        session_manager.lock(message.chat.id, "menu_add")
        session = session_manager.get_user_session(message.chat.id, namespace="menu")
        session["menu_add"] = True
        session_manager.set_user_session(message.chat.id, session, namespace="menu")
        category_class = CategoryClass()
        category_class.handle_category(message)
    except:
        print(traceback.format_exc())


@app.message_handler(func=lambda m: m.text == t(m, "menu_add") and
                     session_manager.get_user_session(m.chat.id, namespace="menu").get("product")
                     and session_manager.can_execute(m.chat.id))
def add_product_handler(message):
    try:
        session_manager.lock(message.chat.id, "product_add")
        add_product(message)
    except:
        print(traceback.format_exc())

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
                        app.send_message(message.chat.id, t(message, "no_categories_to_add_product"), parse_mode="Markdown")
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
            product_bot.cancle_request(message)
            session_manager.unlock(message.chat.id)
            product(message)
        elif session.get("category"):
            session_manager.unlock(message.chat.id)
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

        product_obj = Product.objects.get(code=session.get("code"))
        attributes = product_obj.attributes.all()
        product_handler = ProductHandler(app, product_obj, current_site, attributes=attributes, chat_id=message.chat.id)
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


@app.message_handler(func=lambda message: message.text == t(message, "menu_deactivate")
                    and session_manager.get_user_session(message.chat.id, namespace="menu")["product"] and session_manager.can_execute(message.chat.id))
def deactivate_product(message):
    try:
        if subscription.subscription_offer(message):
            session = session_manager.get_user_session(message.chat.id, namespace="menu")
            session["menu_delete"] = False
            session["menu_"] = False
            session["menu_deactivate"] = True
            profile = ProfileModel.objects.get(tel_id=message.from_user.id)
            if profile.seller_mode:
                if not get_user_store(message).product_store.exists():
                    # Store has no products
                    app.send_message(message.chat.id, t(message, "no_products_to_toggle"))
                    return
                # product_bot.set_state(message.chat.id, product_bot.ProductState.DEACTIVATE)
                session["deavtivate_product"] = True
                markup = send_menu(message, [], "deactivation", [t(message, "cancel_action")])
                app.send_message(message.chat.id, t(message, "enter_product_code_to_deactivate"), reply_markup=markup)
            else:
                app.send_message(message.chat.id, t(message, "not_a_seller_deactivate"))

            session_manager.set_user_session(message.chat.id, session, namespace="menu")
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

@app.message_handler(func=lambda message: message.text == t(message, "my_products_list") and session_manager.can_execute(message.chat.id))
def product_list_method(message):
    try:
        if subscription.subscription_offer(message):
            session_manager.lock(message.chat.id, "product_list")
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
            profile = ProfileModel.objects.get(tel_id=message.chat.id)
            
            # استفاده از تابع t برای ترجمه caption
            caption = t(message, 'product_export_caption', 
                       store_name=result['store_name'],
                       total_products=result['metadata']['total_products'],
                       total_variants=result['metadata']['total_variants'],
                       total_stock_value=result['metadata']['total_stock_value'],
                       currency=t(message, str(profile.preferred_currency)))
            
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
            ##############################
            #attention you can do so
            #from utils.telbot.variables import home_menu
            ##############################
            session_manager.reset_user_session(message.chat.id, namespace="menu")
            session = session_manager.get_user_session(message.chat.id, namespace="menu")
            session['product'] = False
            session['category'] = True
            session_manager.set_user_session(message.chat.id, session, namespace="menu")
            markup = send_menu(message, [t(message, "menu_add"), t(message, "menu_delete"), t(message, "menu_deactivate"), t(message, "edit")], "category", home_menue)
            app.send_message(message.chat.id, t(message, "what_action_on_category"), reply_markup=markup)

        else:
            app.send_message(message.chat.id, t(message, "not_a_seller_edit_categories"))



@app.message_handler(func=lambda m: m.text == t(m, "menu_delete") 
                     and session_manager.get_user_session(m.chat.id, namespace="menu").get("category") and
                     session_manager.can_execute(m.chat.id))
@UltraVideoPrompter(command="menu_delete")
def delete_category_handler(message):
    session = session_manager.get_user_session(message.chat.id, namespace="menu")
    session["menu_delete"] = True
    session["menu_add"] = False
    session["menu_deactivate"] = False
    session_manager.set_user_session(message.chat.id, session, namespace="menu")


    session_manager.lock(message.chat.id, "delete_product")
    category_class = CategoryClass()
    category_class.handle_category(message)




@app.message_handler(func=lambda m: m.text == t(m, "menu_delete") 
                     and session_manager.get_user_session(m.chat.id, namespace="menu")["product"] and
                     session_manager.can_execute(m.chat.id))
def delete_product_handler(message):
    session = session_manager.get_user_session(message.chat.id, namespace="menu")
    session["menu_delete"] = True
    session["menu_add"] = False
    session["menu_deactivate"] = False
    session_manager.set_user_session(message.chat.id, session, namespace="menu")


    session_manager.lock(message.chat.id, "delete_product")
    remove_product(message)


@app.message_handler(func=lambda message: is_category_message(message))
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
        print(f"parent_title: {parent_title}")
        parent = None
        if parent_title:
            parent = Category.objects.filter(pk=parent_title, status=True, store=store).first()
            print(parent)
        

        print(f'parent: {parent}')

        # Create category
        cat = Category.objects.create(
            title=message.text,
            slug=message.text,
            status=True,
            parent=parent,
            store=store
        )

        session["created"] = True

        # Update session (stay in same parent unless user navigates elsewhere)
        if parent:
            session["current_menu"] = cat.title
            print(f"current_menu = cat.title : {cat.title}")
            if parent.parent:
                session["current_category_id"] = parent.parent.id
            else:
                session["current_category_id"] = None
            print(f"current_category_id = cat.id : {cat.id}")
            session["parent_for_new"] = parent.id   # 🔑 keep parent locked
            print(f"parent_for_new = parent.id : {parent.id}")
        else:
            session["current_menu"] = None
            session["current_category_id"] = None
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
@UltraVideoPrompter(command="category")
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
        
        session = session_manager.get_user_session(
            message.chat.id,
            namespace="menu",
        )

        category_class = CategoryClass()

        if session.get("delete_sure"):

            cat = Category.objects.select_related("parent", "store").get(
                pk=session["current_category_id"],
                store__owner__tel_id=message.chat.id,
            )

            parent = cat.parent

            cat.delete()

            if not cat.store.categories.exists():
                category(message)
                return

            if parent:
                if parent.get_all_subcategories():

                    session["current_category_id"] = parent.parent.id
                    session["current_menu"] = parent.title.lower()

                    session_manager.set_user_session(
                        message.chat.id,
                        session,
                        namespace="menu",
                    )

                    message.text = parent.title
                    category_class.handle_subcategory(message)
                    session["current_category_id"] = parent.id

                else:
                    
                    session["current_menu"] = parent.title.lower()
                    

                    if parent.get_all_subcategories():
                        session["current_category_id"] = parent.id
                        message.text = parent.title.lower()
                    else:
                        if parent.parent.parent:
                            session["current_category_id"] = parent.parent.parent.id
                        else:
                            session["current_category_id"] = None
                        message.text = parent.parent.title.lower()


                    session_manager.set_user_session(message.chat.id, session, namespace="menu")
                    category_class.handle_subcategory(message)
                    session["current_category_id"] = parent.parent.id
                    session_manager.set_user_session(message.chat.id, session, namespace="menu")

            else:

                session["current_category_id"] = None
                session["current_menu"] = None

                session_manager.set_user_session(
                    message.chat.id,
                    session,
                    namespace="menu",
                )

                category_class.handle_category(message)

            session["menu_delete"] = True
            session["delete_sure"] = False
            session_manager.set_user_session(message.chat.id, session, namespace="menu")

        elif session.get("deactivate_category_sure"):

            cat = Category.objects.select_related("parent").get(
                pk=session["current_category_id"],
                store__owner__tel_id=message.chat.id,
            )


            cat.status = not cat.status
            cat.save(update_fields=["status"])

            session["category_status_changed"] = [
                cat.status,
                cat.title,
            ]

            parent = cat.parent

            if cat.get_all_subcategories():

                if parent:
                    session["current_category_id"] = cat.parent.id
                else:
                    session["current_category_id"] = None
                session["current_menu"] = cat.title.lower()

                session_manager.set_user_session(
                    message.chat.id,
                    session,
                    namespace="menu",
                )
                message.text = cat.title
                category_class.handle_subcategory(message)
                
                session["current_category_id"] = cat.id

            else:

                if parent:

                    session["current_category_id"] = parent.parent.id

                    session["current_menu"] = cat.title.lower()

                    session_manager.set_user_session(
                        message.chat.id,
                        session,
                        namespace="menu",
                    )

                    message.text = parent.title
                    category_class.handle_subcategory(message)

                    session["current_category_id"] = parent.id

                else:

                    session["current_category_id"] = None
                    session["current_menu"] = None

                    session_manager.set_user_session(
                        message.chat.id,
                        session,
                        namespace="menu",
                    )

                    category_class.handle_category(message)

            session["category_status_changed"] = None
            session["deactivate_category_sure"] = False

        session_manager.unlock(message.chat.id)

        session_manager.set_user_session(
            message.chat.id,
            session,
            namespace="menu",
        )

    except Exception:
        print(traceback.format_exc())


@app.message_handler(func=lambda message: message.text == t(message, "menu_deactivate")
                    and session_manager.get_user_session(message.chat.id, namespace="menu").get("category")
                    and session_manager.can_execute(message.chat.id))
@UltraVideoPrompter(command="menu_deactivate")
def deactivate_category(message):
    try:
        if subscription.subscription_offer(message):
            session = session_manager.get_user_session(message.chat.id, namespace="menu")
            session["menu_delete"] = False
            session["menu_"] = False
            session["menu_deactivate"] = True
            session_manager.set_user_session(message.chat.id, session, namespace="menu")
            profile = ProfileModel.objects.get(tel_id=message.from_user.id)
            store = Store.objects.get(owner=profile)
            if profile.seller_mode:
                session["category_deactivate"] = True
                session_manager.set_user_session(message.chat.id, session, namespace="menu")
                if not Category.objects.filter(store=store).exists():
                    app.send_message(message.chat.id, t(message, "no_categories_for_toggle"))
                    session["category_deactivate"] = False
                    session_manager.set_user_session(message.chat.id, session, namespace="menu")
                    return
                category_class = CategoryClass()
                session_manager.lock(message.chat.id, "menu_add")
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


@app.message_handler(func=lambda message: message.text in [t(message, "edit"),])
def edit(message):
    app.send_message(message.chat.id, t(message, "edit_product_category_soon"))

#####################################   BUILD SHOP  #####################################

@app.message_handler(commands=['build_shop'])
@UltraVideoPrompter(command="build_shop")
def build_shop(message):
    try:
        session = session_manager.get_user_session(message.chat.id, namespace="createshop")
        store_info = SendStore(app)
        profile, store = store_info._load_context(message.chat.id)
        if store:
            text = t("message", "store_settings_panel", profile=profile)
        else:
            text = t("message", "store_opening_panel", profile=profile)
        msg = home(message, text=text, **{"session_delete": ('createshop')})
        session["msg_id"] = msg.message_id
        session_manager.set_user_session(message.chat.id, session, namespace="createshop")
        store_info.show_store_info(message)
    except:
        print(traceback.format_exc())


@app.message_handler(func=lambda message: message.text == t(message, "cancel_action") and session_manager.get_user_session(message.chat.id, namespace="createshop").get("take_data" or None))
def cancle_store_change(message):
    session = session_manager.get_user_session(message.chat.id, namespace="createshop")
    session["take_data"] = False
    session_manager.set_user_session(message.chat.id, session, namespace="createshop")
    build_shop(message)


@app.callback_query_handler(func=lambda call: call.data == "store_name")
def take_name(call):
    build_store = SendStore(app)
    build_store.take_name(call)


@app.message_handler(func=lambda message: session_manager.get_user_session(message.chat.id, namespace="createshop").get("take_name" or None))
def take_name_d(message):
    build_store = SendStore(app)
    profile, store = build_store._load_context(message.chat.id)
    session = session_manager.get_user_session(message.chat.id, namespace="createshop")
    if store:
        store.name = message.text
        store.save()
    else:
        session["take_name_d"] = message.text
    
    session["take_name"] = False
    session["take_data"] = False
    session_manager.set_user_session(message.chat.id, session, namespace="createshop")
    build_shop(message)

       
@app.callback_query_handler(func=lambda call: call.data == "set_store_logo")
def take_logo(call):
    build_store = SendStore(app)
    build_store.take_logo(call)


@app.message_handler(func=lambda message: session_manager.get_user_session(message.chat.id, namespace="createshop").get("take_logo" or None), content_types=['photo'])
def take_logo_d(message):
    try:
        session = session_manager.get_user_session(message.chat.id, namespace="createshop")
        build_store = SendStore(app)
        profile, store = build_store._load_context(message.chat.id)
        if store:
            file_id = message.photo[-1].file_id
            file_info = app.get_file(file_id)
            downloaded_file = app.download_file(file_info.file_path)
            store.logo = ContentFile(downloaded_file, name=f'logo_{store.id}.jpg')
            store.save()
        else:
            file_id = message.photo[-1].file_id
            session["take_logo_d"] = file_id
        
        session["take_logo"] = False
        session["take_data"] = False
        session_manager.set_user_session(message.chat.id, session, namespace="createshop")
        build_shop(message)
    
    except:
       print(traceback.format_exc())


@app.message_handler(func=lambda message: session_manager.get_user_session(message.chat.id, namespace="createshop").get("take_logo" or None))
def take_logo_d_text(message):
    session = session_manager.get_user_session(message.chat.id, namespace="createshop")
    if message.text == t(message, "cancel_action"):
        session["take_logo"] = False
        session_manager.set_user_session(message.chat.id, session, namespace="createshop")
        build_shop(message)
        return
    app.reply_to(message, t(message, "send_only_logo_image"))
    session_manager.set_user_session(message.chat.id, session, namespace="createshop")

@app.callback_query_handler(func=lambda call: call.data == "store_description")
def take_description(call):
    build_store = SendStore(app)
    build_store.take_description(call)

@app.message_handler(func=lambda message: session_manager.get_user_session(message.chat.id, namespace="createshop").get("take_description" or None))
def take_description_d(message):
    try:
        session = session_manager.get_user_session(message.chat.id, namespace="createshop")
        build_store = SendStore(app)
        profile, store = build_store._load_context(message.chat.id)
        if store:
            store.description = message.text
            store.save()
        else:
            session["take_description_d"] = message.text
        
        session["take_description"] = False
        session["take_data"] = False
        session_manager.set_user_session(message.chat.id, session, namespace="createshop")
        build_shop(message)
    
    except:
       print(traceback.format_exc())



@app.callback_query_handler(func=lambda call: call.data == "store_telegram_channel")
# @subscription_required()
def take_telegram_channel(call):
    build_store = SendStore(app)
    build_store.take_telegram_channel(call)


@app.message_handler(func=lambda message: session_manager.get_user_session(message.chat.id, namespace="createshop").get("take_telegram_channel" or None))
def take_telegram_channel_d(message):
    try:
        session = session_manager.get_user_session(message.chat.id, namespace="createshop")
        build_store = SendStore(app)
        profile, store = build_store._load_context(message.chat.id)
        if str(message.text).startswith("@") or str(message.text).startswith("t.me/") or str(message.text).startswith("https://t.me/"):
            text = str(message.text).replace("@", "")
            text = text.replace("https://t.me/", "")
            text = text.replace("t.me/", "")
            text = "@" + text
        else:
            text = "@" + message.text
        if store:
            store.tel_channel = text
            store.save()
        else:
            session["take_telegram_channel_d"] = text
        
        session["take_telegram_channel"] = False
        session["take_data"] = False
        session_manager.set_user_session(message.chat.id, session, namespace="createshop")
        build_shop(message)
    
    except:
       print(traceback.format_exc())




@app.callback_query_handler(func=lambda call: call.data == "delete_store")
def delete_store(call):
    try:
        build_store = SendStore(app)
        profile, store = build_store._load_context(call.message.chat.id)
        store.delete()
        back_to_buyer(call.message, text=t(call.message, "store_deleted_successfully"))

    except:
        print(traceback.format_exc())



@app.callback_query_handler(func=lambda call: call.data == "store_payment_method")
def store_payment_method(call):
    try:
        send_store = SendStore(app)
        
        send_store.payment_mehtod(call)
    except:
        print(traceback.format_exc())

    
@app.callback_query_handler(func=lambda call: session_manager.get_user_session(call.message.chat.id, namespace="createshop").get("take_payment_method"))
def store_payment_method_zarinpal(call):
    try:
        send_store = SendStore(app)
        session = session_manager.get_user_session(call.message.chat.id, namespace="createshop")
        app.edit_message_text(chat_id=call.message.chat.id, text = t(call.message, "enter_iban"), message_id=call.message.message_id, reply_markup=None)
        session["take_payment_method"] = False
        session["take_iban"] = True
        session_manager.set_user_session(call.message.chat.id, session, namespace="createshop")
        send_store.payment_mehtod_take_iban(call)
    except:
        print(traceback.format_exc())

@app.message_handler(func=lambda message: session_manager.get_user_session(message.chat.id, namespace="createshop").get("take_iban"))
def store_payment_method_take_iban(message):
    try:
        send_store = SendStore(app)
        session = session_manager.get_user_session(message.chat.id, namespace="createshop")
        profile, store = send_store._load_context(message.chat.id)
        
        iban = message.text.strip()
        if not iban:
            app.send_message(message.chat.id, t(message, "merchant_code_cannot_be_empty"), alert=False)
            return
        
        if store:
            store.iban = iban
            store.save()
        else:
            session["take_iban_d"] = iban

        session["take_iban"] = False
        session["take_data"] = False
        session_manager.set_user_session(message.chat.id, session, namespace="createshop")
        build_shop(message)

    except:
        print(traceback.format_exc())


@app.callback_query_handler(func=lambda call: call.data == "submit_info")
def submit_store(call):
    try:
        session = session_manager.get_user_session(call.message.chat.id, namespace="createshop")
        temp_address_session = session_manager.get_user_session(call.message.chat.id, namespace="temp_address") or {}
        build_store = SendStore(app)
        profile, store = build_store._load_context(call.message.chat.id)
        msg = {"take_logo_d": t("message", "store_logo", profile=profile),
               "take_name_d": t("message", "name", profile=profile),
               "take_telegram_channel_d": t("message", "telegram_channel", profile=profile),
               "take_description_d": t("message", "store_description", profile=profile),
               }

        for i in msg:
            if not session.get(f"{i}"):
                if i == "store_description":
                    msg_info = t("message", "store_description_not_set", profile=profile)
                    app.answer_callback_query(call.id, msg_info, show_alert=True)
                    return
                item = str(msg[i])
                msg_info = t("message", "store_info_not_filled_yet", profile=profile, item=item)
                app.answer_callback_query(call.id, msg_info, show_alert=True)
                return
        
        file_id = session.get("take_logo_d")
        file_info = app.get_file(file_id)
        downloaded_file = app.download_file(file_info.file_path)
        store = Store.objects.create(
            owner = profile,
            name=session.get("take_name_d"),
            tel_channel=session.get("teke_telegram_channel_d"),
            lang=profile.lang,
            description=session.get("take_description_d"),
            status=False,
            iban=session.get("take_iban_d")
        )
        address = Address.objects.create(store=store, shipping_line1=temp_address_session["selected_address_line1"], shipping_country=temp_address_session["selected_country"], shipping_province=temp_address_session["selected_province"], shipping_city=temp_address_session["selected_city"], shipping_zip_code=temp_address_session["selected_zipcode"])
        from subscription.services.general import SubscriptionService
        session_manager.reset_user_session(call.message.chat.id, namespace="temp_address")
        subscription = SubscriptionService.get_or_create_subscription(store)
        store.logo=ContentFile(downloaded_file, name=f'logo_{store.id}.jpg')
        store.save()
        app.send_message(call.message.chat.id, t("message", "store_registered_successfully", profile=profile))
        session["take_data"] = False
        session_manager.set_user_session(call.message.chat.id, session, namespace="createshop")  
        become_a_seller(call.message)

    except:
        print(traceback.format_exc())



##################################### PROMOTION #####################################

@app.message_handler(commands=['promote'])
def promotion(message):
    try:
        promote = Promote(app)
        promote._show_offer(message.chat.id)
    except:
        print(traceback.format_exc())


router = PromoteRouter()
promote = Promote(app)
# ✅ اول register کن
router.register("plan", "next", promote._handle_plan_next)
router.register("plan", "prev", promote._handle_plan_prev)

router.register("duration", "next", promote._handle_duration_next)
router.register("duration", "prev", promote._handle_duration_prev)

router.register("subscribe", "any", promote.handle_subscribe)

@app.callback_query_handler(func=lambda call: call.data.startswith("promote"))
def plan_navigation(data):

    try:

        promote = Promote(app)

        # ✅ بعد dispatch کن
        router.dispatch(data)

    except:
        print(traceback.format_exc())





##################################### END CATEGROY #####################################

# hadling any unralted message
@app.message_handler(func=lambda message: app.get_state(user_id=message.from_user.id, chat_id=message.chat.id) is None)
def handle_message(message):
    if session_manager.is_locked(message.chat.id):
        return
    if subscription.subscription_offer(message):
        app.send_message(message.chat.id, t(message, "command_not_found"))



# Handling the callback query when the 'answer' button is clicked
@app.callback_query_handler(func=lambda call: call.data == "پاسخ")
def answer(call):
    try:
        clean_text = BeautifulSoup(
            call.message.text, "html.parser"
        ).get_text()

        pattern = t(call, "received_message_pattern")

        match = re.search(pattern, clean_text)

        if not match:
            app.send_message(
                call.message.chat.id,
                "خطا: شناسه کاربر پیدا نشد."
            )
            return

        user = int(match.group(1))

        app.send_message(
            chat_id=call.message.chat.id,
            text=t(call.message, "send_answer_to", user_id=user),
            reply_markup=types.ForceReply(),
            parse_mode="HTML"
        )

        app.set_state(
            user_id=call.from_user.id,
            state=Support.respond,
            chat_id=call.message.chat.id
        )

    except Exception:
        print(traceback.format_exc())




@app.callback_query_handler(func=lambda call: call.data == t(call.message, "end_chat"))
def terminate_chat(call):
    if subscription.subscription_offer(call.message):
        try:
            app.delete_state(user_id=call.from_user.id, chat_id=call.message.chat.id)
            app.send_message(chat_id=call.message.chat.id, text=t(call.message, "conversation_ended"))
        except Exception as e:
            error_message = traceback.format_exc()
            print(f"your error is: {error_message}")




# Handling the support agent's reply message which is saved in 'Support.respond' state
@app.message_handler(state=Support.respond,
                     func=lambda message: message.reply_to_message and 
                                          message.reply_to_message.text and 
                                          message.reply_to_message.text.startswith(t(message, "send_answer_to", chat_id=message.chat.id)[:10]))
def answer_text(message):
    try:        
        # بررسی reply_to_message
        if not message.reply_to_message:
            print("❌ ERROR: No reply_to_message")
            app.send_message(message.chat.id, "خطا: این پیام باید در پاسخ به پیام قبلی ارسال شود.")
            home(message)
            return
                    
        # پردازش متن
        clean_text = BeautifulSoup(message.reply_to_message.text, "html.parser").get_text()
        
        # نرمال‌سازی
        normalized_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        # دریافت الگو - با دیباگ بیشتر
        try:
            pattern = t(message, "pattern")
            
            # بررسی خود تابع t
            try:
                # بررسی زبان کاربر
                lang = ProfileModel.objects.get(tel_id=message.from_user.id).lang
                
                # بررسی ترجمه‌ها
                if "pattern" in translations:
                    pattern_dict = translations["pattern"]
            except Exception as e:
                print(f"Error checking translations: {e}")
                
        except Exception as t_error:
            print(f"❌ ERROR in t() function: {t_error}")
            import traceback
            traceback.print_exc()
            # Fallback pattern
            pattern = r"Send your answer to \d+"
            print(f"Using fallback pattern: '{pattern}'")
        
        # تست تطابق الگو
        
        match = re.search(pattern, normalized_text)
        
        if match:            
            # استخراج عدد
            number_match = re.search(r"\d+", match.group())
            if number_match:
                user_id = number_match.group()
            else:
                # جستجوی مستقیم
                all_numbers = re.findall(r"\d+", normalized_text)
                if all_numbers:
                    user_id = all_numbers[0]
                else:
                    raise ValueError("No user ID found")
        else:
            print("❌ PATTERN NOT MATCHED!")
            # جستجوی مستقیم برای عدد
            all_numbers = re.findall(r"\d+", normalized_text)
            print(f"All numbers in text: {all_numbers}")
            
            if all_numbers:
                user_id = all_numbers[0]
                print(f"Using first number: {user_id}")
            else:
                print("❌❌ NO NUMBERS FOUND!")
                raise ValueError("No user ID found in message")
        
        # تبدیل به عدد
        try:
            user = int(user_id)
        except ValueError:
            raise ValueError(f"Invalid user ID: {user_id}")
                
        
        try:
            user_message = texts.get(user)
            if user_message:
                
                response_text = t(message, "support_reply_with_message", user_message=escape_special_characters(user_message), support_answer=escape_special_characters(message.text))
                app.send_message(chat_id=user, text=response_text, parse_mode="HTML")
                
                # حذف از حافظه
                del texts[user]
            else:
                print(f"⚠️ No original message found for user {user}")
                response_text = f"Support answer:\n<b>{escape_special_characters(message.text)}</b>"
                app.send_message(chat_id=user, text=response_text, parse_mode="HTML")
                print("✅ Message sent without original text")
            
            # ارسال تأیید
            confirmation_msg = t(message, "message_sent")
            app.send_message(chat_id=message.chat.id, text=confirmation_msg)
            
            # حذف state
            app.delete_state(user_id=message.from_user.id, chat_id=message.chat.id)
            
        except Exception as process_error:
            print(f"❌ Error in processing: {process_error}")
            raise
        
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌❌❌ FINAL EXCEPTION IN answer_text:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print(f"Full traceback:")
        import traceback
        traceback.print_exc()
        
        # پیام خطای واضح‌تر
        if "No user ID found" in str(e):
            error_msg = "خطا: شناسه کاربر در پیام یافت نشد. لطفاً دوباره تلاش کنید."
        elif "Invalid user ID" in str(e):
            error_msg = f"خطا: شناسه کاربر نامعتبر است."
        else:
            error_msg = f"خطا در پردازش:\n<code>{type(e).__name__}: {str(e)[:100]}</code>"
        
        app.send_message(chat_id=message.chat.id, text=error_msg, parse_mode="HTML")
    
    finally:
        home(message)



##################################

#####################################################################################################
# Functions for specific actions


# show balance
from wallets.services import wallet_summary


def show_balance(message):

    try:

        if subscription.subscription_offer(message):

            profile = ProfileModel.objects.get(
                tel_id=message.from_user.id,
            )

            summary = wallet_summary(
                wallet=profile.wallet,
                currency=profile.preferred_currency,
            )

            app.send_message(

                message.chat.id,

                t(
                    message,
                    "user_balance",

                    available=f"{summary['available']:,.0f}",
                    pending=f"{summary['pending']:,.0f}",
                    locked=f"{summary['locked']:,.0f}",
                    total=f"{summary['total']:,.0f}",

                    currency=profile.preferred_currency.symbol,
                ),
            )

    except Exception:

        app.send_message(
            message.chat.id,
            traceback.format_exc(),
        )
    

def ask_for_product_code(message):
    if subscription.subscription_offer(message):
        app.send_message(message.chat.id, t(message, "enter_product_code_to_search"))
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
            ##############################
            #attention you can do so
            #from utils.telbot.variables import home_menu
            ##############################

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



###################### SERIALIZERS ########################


from rest_framework import viewsets, permissions
from .models import ConversationModel, MessageModel, CachedMedia
from .serializers import ConversationSerializer, MessageSerializer, CachedMediaSerializer

class ConversationViewSet(viewsets.ModelViewSet):
    queryset = ConversationModel.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class MessageViewSet(viewsets.ModelViewSet):
    queryset = MessageModel.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class CachedMediaViewSet(viewsets.ModelViewSet):
    queryset = CachedMedia.objects.all()
    serializer_class = CachedMediaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


