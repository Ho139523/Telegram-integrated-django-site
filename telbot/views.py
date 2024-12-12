#General imports
from telebot import TeleBot


# Variables imports
from utils.variables.TOKEN import TOKEN

# start handler imports
import requests


# start: KeyboardButtton for forced subscription
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from utils.variables.CHANNELS import my_channels_with_atsign, my_channels_without_atsign


#signup
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


# Defining the app
app = TeleBot(token=TOKEN)

# Server side
import json
import telebot.types
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import logging

logger = logging.getLogger(__name__)
from django.views.decorators.csrf import csrf_exempt
import subprocess
from utils.telbot.functions import *
localtunnel_password = get_tunnel_password()
current_site = get_current_site()
current_webhook = get_current_webhook()





# Webhook settings
logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class TelegramBotWebhookView(View):
    def post(self, request, *args, **kwargs):
        try:
            json_str = request.body.decode('UTF-8')
            logger.info(f"Received data: {json_str}")  # لاگ درخواست دریافتی
            update = telebot.types.Update.de_json(json.loads(json_str))
            app.process_new_updates([update])  # پردازش پیام توسط ربات
            return JsonResponse({"status": "success"}, status=200)
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=200)  # همیشه HTTP 200 برگردانید
            
            

# Check subscription
def check_subscription(user, channels=my_channels_with_atsign):
    for channel in channels:
        is_member = app.get_chat_member(chat_id=channel, user_id=user)
        
        if is_member.status in ["kicked", "left"]:
            
            return False
        
        return True
        

@app.callback_query_handler(func=lambda call: call.data == 'check_subscription')
def handle_check_subscription(call):
    is_member = check_subscription(user=call.from_user.id)
    if is_member:
        app.answer_callback_query(call.id, "تشکر! عضویت شما تایید شد.")
        app.send_message(call.message.chat.id, "🎉 عضویت شما تایید شد. حالا می‌توانید از امکانات ربات استفاده کنید.")
    else:
        app.answer_callback_query(call.id, "لطفاً ابتدا در کانال یا گروه عضو شوید.")




# start handler
@app.message_handler(commands=['start'])
def start(message):
    
    # User Info
    tel_id = message.from_user.username if message.from_user.username else message.from_user.id
    tel_name = message.from_user.first_name

    # Make a POST request to the registration API
    response = requests.post(f"{current_site}/api/check-registration/", json={"tel_id": tel_id})
    
    # Markup keyboards
    
    channel_markup= InlineKeyboardMarkup()
    check_subscription_button = InlineKeyboardButton(
        text='عضو شدم.', 
        callback_data='check_subscription'  # Callback data for interaction
    )
    channel_subscription_button = InlineKeyboardButton(
        text='در کانال ما عضو شوید ...', 
        url=f"https://t.me/{my_channels_without_atsign[0]}"  # Replace with your Telegram channel link
    )
    group_subscription_button = InlineKeyboardButton(
        text="در گروه ما عضو شوید ...", 
        url=f"https://t.me/{my_channels_without_atsign[1]}"  # Replace with your Telegram group link
    )
    channel_markup.add(channel_subscription_button, group_subscription_button)
    channel_markup.add(check_subscription_button)

    # Handle the response based on status code
    if response.status_code == 201:
        app.send_message(
            message.chat.id,
            f"🏆 {tel_name} عزیز ثبت نامت تو ربات کتونی اوریجینال با موفقیت انجام شد.\n\n"
            f"🔔 از حالا ما نام کاربری تلگرام شما رو در دیتابیس خودمون داریم و اگر تمایل داشته باشید "
            f"می تونیم با توجه به علایق تون سلیقه شما رو با هوش مصنوعی پیش بینی کنیم و علاوه بر محصولاتی "
            f"که در کانال ما می بینید، مورد علاقه های تان را برای شما در ربات ارسال کنیم.\n\n"
        )
    else:
        app.send_message(
            message.chat.id,
            f"{tel_name}\n عزیز شما قبلا در ربات کتونی اوریجینال ثبت نام کردید.\n\n"
        )
        
    try:
        is_member = check_subscription(user=message.from_user.id)
            
        if is_member==False:
            app.send_message(message.chat.id, "متاسفانه شما در کانال یا گروه ما عضو نیستید...\n\n برای استفاده از ربات در گروه و کانال زیر عضو شوید.", reply_markup=channel_markup)
        
        else:
            pass
            
    except Exception as e:
        print(f'error is: {e}')
