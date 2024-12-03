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
from django.views.decorators.csrf import csrf_exempt
import subprocess
from utils.telbot.functions import *
localtunnel_password = get_tunnel_password()
current_site = get_current_site()
current_webhook = get_current_webhook()




# Webhook settings
@method_decorator(csrf_exempt, name='dispatch')
class TelegramBotWebhookView(View):
    def post(self, request, *args, **kwargs):
        try:
            json_str = request.body.decode('UTF-8')
            logger.info(f"Received data: {json_str}")  # Log the received data
            update = telebot.types.Update.de_json(json.loads(json_str))
            app.process_new_updates([update])
            return JsonResponse({"status": "success"})
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
            
            

# start handler
@app.message_handler(commands=['start'])
def start(message):
    tel_id = message.from_user.username
    tel_name = message.from_user.name
    response = requests.post(f"{current_site}/api/check-registration/", json={"tel_id": tel_id})
    
    if response.status_code == 201:
        app.send_message(message.chat.id, f"🏆 {tel_name}عزیز ثبت نامت تو ربات کتونی اوریجینال با موفقیت انجام شد.\n\n🔔 از حالا ما نام کاربری تلگرام شما رو در دیتابیس خودمون داریم و اگر تمایل داشته باشید می تونیم با توجه به علایق تون سلیقه شما رو با هوش مصنوعی پیش بینی کنیم و علاوه بر محصولاتی که در کانال ما می بینید، مورد علاقه های تان را برای شما در ربات ارسال کنیم.\n\n🙏🙏🙏 خوشحالیم که شما رو در جمع خودمون داریم.")
    else:
        app.send_message(message.chat.id, f'{message.from_user.name}\n عزیز شما قبلا در ربات کتونی اوریجینال ثبت نام کردید.\n\nما نام کاربری تلگرام شما رو در دیتابیس خودمون داریم و اگر تمایل داشته باشید می‌تونیم با توجه به علایق‌تون سلیقه شما رو با هوش مصنوعی پیش‌بینی کنیم و علاوه بر محصولاتی که در کانال ما می‌بینید، مورد علاقه‌های‌تان را برای شما در ربات ارسال کنیم.\n\n')