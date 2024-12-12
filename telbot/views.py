#General imports
from telebot import TeleBot


# Variables imports
from utils.variables.TOKEN import TOKEN

# start handler imports
import requests


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
            
            

# start handler
@app.message_handler(commands=['start'])
def start(message):
    tel_id = message.from_user.username if message.from_user.username else message.from_user.id
    tel_name = message.from_user.first_name

    # Make a POST request to the registration API
    response = requests.post(f"{current_site}/api/check-registration/", json={"tel_id": tel_id})
    
    try:
        # Print the JSON response for debugging
        print("Response JSON:", response.json())  # Use .json() to access the response as a dictionary
    except ValueError:
        # Handle cases where the response is not JSON
        print("Response Text:", response.text)

    # Handle the response based on status code
    if response.status_code == 201:
        print('hh1')
        app.send_message(
            message.chat.id,
            f"🏆 {tel_name} عزیز ثبت نامت تو ربات کتونی اوریجینال با موفقیت انجام شد.\n\n"
            f"🔔 از حالا ما نام کاربری تلگرام شما رو در دیتابیس خودمون داریم و اگر تمایل داشته باشید "
            f"می تونیم با توجه به علایق تون سلیقه شما رو با هوش مصنوعی پیش بینی کنیم و علاوه بر محصولاتی "
            f"که در کانال ما می بینید، مورد علاقه های تان را برای شما در ربات ارسال کنیم.\n\n🙏🙏🙏 خوشحالیم که شما رو در جمع خودمون داریم."
        )
    else:
        print("hh2")
        try:
            app.send_message(
                message.chat.id,
                f"{message.from_user.first_name}\n عزیز شما قبلا در ربات کتونی اوریجینال ثبت نام کردید.\n\n"
                f"ما نام کاربری تلگرام شما رو در دیتابیس خودمون داریم و اگر تمایل داشته باشید "
                f"می‌تونیم با توجه به علایق‌تون سلیقه شما رو با هوش مصنوعی پیش‌بینی کنیم و علاوه بر محصولاتی "
                f"که در کانال ما می‌بینید، مورد علاقه‌های‌تان را برای شما در ربات ارسال کنیم.\n\n"
            )
        except Exception as e:
            print(f"Error sending message: {e}")
