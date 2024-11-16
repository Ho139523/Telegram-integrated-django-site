from django.shortcuts import render
from django.views.generic import View
import telebot
import random
from django.http import JsonResponse
import json
import requests
import logging
from .models import telbotid
import re
from accounts.models import User
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import telbotid
from accounts.models import ProfileModel
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

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

# Server side
#import subprocess

# Creating the object 
TOKEN = "7777543551:AAHJYYN3VwfC686y1Ir_aYewX1IzUMOlU68"
bot = telebot.TeleBot(TOKEN)  # Replace with your actual token  

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class TelegramBotWebhookView(View):
    def post(self, request, *args, **kwargs):
        try:
            json_str = request.body.decode('UTF-8')
            logger.info(f"Received data: {json_str}")  # Log the received data
            update = telebot.types.Update.de_json(json.loads(json_str))
            bot.process_new_updates([update])
            return JsonResponse({"status": "success"})
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)


# Writing the functions  


# localtunnel getting password

#def get_tunnel_password():
#    try:
#        result = subprocess.run(
 #           ["curl", "-s", "https://loca.lt/mytunnelpassword"],
#            stdout=subprocess.PIPE,
#            stderr=subprocess.PIPE,
#            text=True
#        )
#        if result.returncode == 0:
 #           password = result.stdout.strip()  # حذف فاصله‌ها و خط‌های اضافی
#            return password
#        else:
#            print("Error fetching password:", result.stderr)
#            return None
#    except Exception as e:
#        print(f"An error occurred: {e}")
#        return None

# استفاده از تابع
localtunnel_password = get_tunnel_password()


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
        
current_site = get_current_site()
current_webhook = get_current_webhook()

print(current_site)


# Start and Welcome  
@bot.message_handler(commands=["start"])  
def wellcome(message, current_site=current_site):  
    
    # Buttons
    
    markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    signup_button = KeyboardButton(text='از همین جا در سایت ثبت نام می کنم')
    skip_button = KeyboardButton(text='حوصله ندارم بعدا ثبت نام می کنم همین طوری ادامه بده')
    markup.add(signup_button, skip_button)
    
    
    
      
    if message.from_user.username not in [item['tel_id'] for item in telbotid.objects.values("tel_id")]+[item['telegram'] for item in ProfileModel.objects.values("telegram")]:
        # Create a new telbotid instance without a user  
        new_telbotid = telbotid(user=None, tel_id=message.from_user.username)
        
        # Save the instance to the database  
        new_telbotid.save()
        
        bot.send_message(message.chat.id, '⭕️ سلام\n\n امیدوارم حالت توپ توپ باشه 🤌 \n\n 🔥💯 اینجا ربات کتونی اوریجینال هست و توش می تونی یه دنیا کفش و کتونی اصل که از گمرک میاد رو پیدا کنی.\n\n 💬 فقط کافیه کد کالا رو داشته باشی تا مراحل ثبت سفارش رو با هم اینجا انجام بدیم.\n\n توی کانال می‌تونی محصولات رو ببینی این آدرس کانال ماست یه سر بهش بزن:\n \n @sneakers_ir')
        bot.send_message(message.chat.id, "🏆 عزیزم ثبت نامت تو ربات کتونی اوریجینال با موفقیت انجام شد.\n\n🔔 از حالا ما نام کاربری تلگرام شما رو در دیتابیس خودمون داریم و اگر تمایل داشته باشید می تونیم با توجه به علایق تون سلیقه شما رو با هوش مصنوعی پیش بینی کنیم و علاوه بر محصولاتی که در کانال ما می بینید، مورد علاقه های تان را برای شما در ربات ارسال کنیم.\n\n🙏🙏🙏 خوشحالیم که شما رو در جمع خودمون داریم.")
    
    else:
        bot.send_message(message.chat.id, f'{message.from_user.username}\n عزیز شما قبلا در ربات کتونی اوریجینال ثبت نام کردید.\n\nما نام کاربری تلگرام شما رو در دیتابیس خودمون داریم و اگر تمایل داشته باشید می‌تونیم با توجه به علایق‌تون سلیقه شما رو با هوش مصنوعی پیش‌بینی کنیم و علاوه بر محصولاتی که در کانال ما می‌بینید، مورد علاقه‌های‌تان را برای شما در ربات ارسال کنیم.\n\n')
        
        
    # Add the user username to the telbotid class if existed in ProfileModel
    if message.from_user.username not in [item['telegram'] for item in ProfileModel.objects.values("telegram")]:
        bot.send_message(
            message.chat.id,
            f"🥰😍🥰 البته که داشتن شما در ربات برای ما افتخاره اما پس از بررسی مجدد متوجه شدم شما در سایت ما عضو نیستید ... 🥲🥺\n\n"
            f"💢 یادت باشه اگه از توی ربات در سایت ثبت نام کنی می تونی تا پنج روز عضویت ویژه داشته باشی و به همه محتواهای پولی سایت دسترسی داشته باشی، "
            f"توی سایت می تونی تمام محصولات رو یک جا ببینی و در همون جا در سبد خرید حساب کاربری خودت مورد علاقه هات رو اضافه کنی تا هر موقع خواستی به درگاه پرداخت وصل شی و پس از پرداخت کفش هات رو درب منزل تحویل بگیری.\n\n"
            f"{current_site}"
            f"{f'\n\n💡 توجه! اگر از شما رمز درخواست شد، از این کد استفاده کنید:\n\n🔑 {localtunnel_password}' if 'loca.lt' in current_site else ''}",
            reply_markup=markup
        )

        

# هندلر برای دکمه "ثبت نام می‌کنم"
@bot.message_handler(func=lambda message: message.text == "از همین جا در سایت ثبت نام می کنم")
def ask_username(message):
    bot.send_message(message.chat.id, "ممکنه لطفا ایمیلت رو وارد کنی:")
    bot.register_next_step_handler(message, pick_email)
    
# email validation
def is_valid_email(email):  
    # Regular expression for validating an Email  
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'  
    
    # Use re.match to check if the email matches the pattern  
    if re.match(email_pattern, email):  
        return True, 'احسنت! این درسته.\n\n حالا بریم برای نام کاربری،\n یه نام کاربری خوب که بقیه از قبل انتخابش نکرده باشن برای خودت انتخاب کن:'
    else:  
        return False, "داداش گلم خدایی این شبیه آدرس ایمیله؟؟؟\n\n یه جایی ازش ایراد داره به نظرم! بگرد پیداش کن درستش کن دوباره برام بنویسش:"


# گرفتن آدرس ایمیل
def pick_email(message):    
    email = message.text
    
    is_valid, validation_message = is_valid_email(email)  # Assign directly to validation_message
    
    if email in [item['email'] for item in User.objects.values("email")]:
        bot.send_message(message.chat.id, "این ایمیل که قبلا ثبت نام کرده که! می خوای با یه ایمیل دیگه ات امتحان کن:")
        bot.register_next_step_handler(message, pick_email)  # Prompt again for email
    else:
        if is_valid:
            bot.send_message(message.chat.id, validation_message)  # This now uses validation_message correctly
            bot.register_next_step_handler(message, pick_username, email)  # Proceed to username prompt
        else:
            bot.send_message(message.chat.id, validation_message)  # Re-prompt for a valid email
            bot.register_next_step_handler(message, pick_email)  # Prompt again for email

    
    

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


# دریافت نام کاربری
def pick_username(message, email):
    username = message.text
    is_valid, validation_message = validate_username(username)  # Validation message is now separate from `message`
    
    # Send validation message
    bot.send_message(message.chat.id, validation_message)
    
    if is_valid:
        # Check if username already exists
        if username in [item['username'] for item in User.objects.values("username")]:
            bot.send_message(message.chat.id, "متاسفانه نام کاربری که انتخاب کردی از قبل انتخاب شده لطفا یکی دیگه رو امتحان کن:")
            bot.register_next_step_handler(message, pick_username, email)
        else:
            bot.send_message(message.chat.id, "عالیه! حالا یه رمز عبور هشت رقمی شامل حروف برزگ و کوچک عدد و یکی از علامت‌ها برای خودت انتخاب کن:")
            bot.register_next_step_handler(message, pick_password, email, username)
    else:
        # If the username is invalid, re-prompt the user
        bot.register_next_step_handler(message, pick_username, email)

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

# تعیین رمز عبور
def pick_password(message, email, username):
    password = message.text
    is_valid, validation_message = validate_password(password)
    
    # Send validation message
    bot.send_message(message.chat.id, validation_message)
    
    # If password is valid, proceed with registration
    if is_valid:
        
        bot.send_message(message.chat.id, "دمت گرم! حالا یه بار دیگه رمزت رو برام بزن تا تاییدش کنم و این بشه رمز عبورت:")
        bot.register_next_step_handler(message, pick_password2, email, username, password)
        
    
    # If password is not valid, ask for a new one
    else:
        bot.register_next_step_handler(message, pick_password, email, username)
        
        
# تایید رمز
def pick_password2(message, email, username, password, current_site=current_site):
    password2 = message.text
    
    if password2 == password:
        # Django's user model
        User = get_user_model()
        
        # Set special_user to five days from now  
        special_user_date = timezone.now() + timedelta(days=5)
        
        
        # Create user in Django
        user = User.objects.create(
            username=username,
            email=email,
            password=make_password(password),  # Hash the password
            special_user=special_user_date,  # Set the date to five days from now  
            is_active=False  # Keep inactive until email activation
        )
        
        ProfileModel.objects.create(user=user, fname=message.from_user.first_name, lname=message.from_user.last_name, telegram=username)

        # Trigger activation email
        current_site = current_site # Replace with your actual site domain
        mail_subject = 'Activation link has been sent to your email id'
        message_content = render_to_string('registration/acc_active_email.html', {
            'user': user,
            'domain': current_site[8:],
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': generate_token.make_token(user),
        })
        
        email = EmailMessage(
            mail_subject, message_content, to=[email]
        )
        email.send()

        bot.send_message(
            message.chat.id, 
            f"حالا دیگه حساب کاربری خودت رو تو وبسایت هم داری ثبت نام با موفقیت انجام شد! {username} عزیز، خوش آمدی! 🎉\n\n"
            f"یه سر به سایت بزن و به حسابت ورود کن.\n\n"
            f"آدرس سایت رو دوباره برات این پایین گذاشتم.👇👇👇\n\n"
            f"{current_site}"
            f"{f'\n\n💡 توجه! اگر از شما رمز درخواست شد، از این کد استفاده کنید:\n\n🔑 {localtunnel_password}' if 'loca.lt' in current_site else ''}"
        )

        
        bot.send_message(message.chat.id, "دوست داری نمایه خودت رو مثل اطلاعات دقیق تر از خودت تکمیل کنی یا ترجیح می دی تو سایت این کار رو بکنی؟")
        bot.register_next_step_handler(message, )
    else:
        bot.send_message(message.chat.id, "تایید رمز عبور باید با خود آن یکی باشد. دوباره تایید رمز عبور را وارد کنید:")
        bot.register_next_step_handler(message, pick_password2, email, username, password)


# هندلری برای دکمه پروفایل
# @bot.message_handler(func=lambda message: message.text == "نمایه ام رو کامل می کنم")
# def ask_username(message):
    # bot.send_message(message.chat.id, "ممکنه لطفا ایمیلت رو وارد کنی:")
    # bot.register_next_step_handler(message, pick_email)

# Handlers for different content types  
@bot.message_handler(content_types=["audio"])  
def audio_handler(message):  
    bot.reply_to(message, "ممنون از آهنگی که فرستادی:)\n\nاما من برای گوش کردن آهنگ اینجا نیستم.\n\n من اینجا می خوام کمکت کنم کتونی و کفش خودت رو پیدا کنی.")  

@bot.message_handler(content_types=["document"])  
def document_handler(message):  
    bot.reply_to(message, "ممنون که برام سند فرستادی:)\n\nاما من هنوز نمی تونم اینا ها رو تحلیل کنم.\n\n در آینده نه چندان دور قراره که با هوش مصنوعی بتونم تحلیل کنم چیزایی رو که می فرستی.\n\n من اینجا هستم که کمکت کنم کتونی و کفش خودت رو پیدا کنی.")  

@bot.message_handler(content_types=['voice'])  
def voice_handler(message):  
    bot.reply_to(message, "ممنون که برام ویس فرستادی:)\n\nاما من هنوز نمی تونم ویس ها رو تحلیل کنم.\n\n در آینده نه چندان دور قراره که با هوش مصنوعی بتونم تحلیل کنم چیزایی رو که می فرستی.")  
    
@bot.message_handler(content_types=['location'])  
def location_handler(message):  
    bot.reply_to(message, "ممنون که برام موقعیت مکانی ات رو فرستادی:)\n\nاما موقعیت مکانی تو وقتی ثبت سفارش کردی به درد من می خوره تا بتونم کالا رو راحت تر بهت برسونم.")  

@bot.message_handler(content_types=['contact'])  
def contact_handler(message):  
    bot.reply_to(message, "ممنون که برام شماره تماست رو فرستادی:)\n\nاما شماره تو وقتی ثبت سفارش کردی به درد من می خوره تا بتونم باهات در ارتباط باشم.")  

@bot.message_handler(content_types=['animation'])  
def animation_handler(message):  
    sos_must = ["سس ماست", "خو الآن که چی مثلا", "😑🙄", "اسکولمون کردی؟", "اومدی کفش بخری یا بخندونی مون اگه الافیم بگو بریم سراغ کارمون"]  
    function = lambda text: random.choice(text)  
    bot.reply_to(message, function(sos_must))  
    
@bot.message_handler(content_types=['text'])  
def text_handler(message):  
    bot.reply_to(message, "در آینده نزدیک قراره بتونم متنی که برام می فرستی رو تحلیل کنم و جوابت رو بدم اما هنوز به این قابلیت مسلح نشدم.")  
    bot.send_message(message.chat.id, "🤫")  
    
@bot.message_handler(content_types=['sticker'])  
def sticker_handler(message):  
    sos_must = ["سس ماست", "خو الآن که چی مثلا", "😑🙄", "اسکولمون کردی؟", "اومدی کفش بخری یا بخندونی مون اگه الافیم بگو بریم سراغ کارمون"]  
    function = lambda text: random.choice(text)  
    bot.reply_to(message, function(sos_must))  

# Running the bot  
# bot.polling()
