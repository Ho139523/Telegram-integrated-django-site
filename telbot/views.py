# General imports
from telebot import TeleBot
import json
import telebot.types
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import requests
import logging

# Variables imports
from utils.variables.TOKEN import TOKEN
from utils.variables.CHANNELS import my_channels_with_atsign, my_channels_without_atsign

# Initialize the bot
app = TeleBot(token=TOKEN)

logger = logging.getLogger(__name__)

# Helper function: Determine if the user is from a specific country
def get_user_country(ip):
    try:
        response = requests.get(f"https://ipapi.co/{ip}/json/")
        if response.status_code == 200:
            return response.json().get("country_name")
    except Exception as e:
        logger.error(f"Error determining IP location: {e}")
    return None

# Webhook settings
@method_decorator(csrf_exempt, name='dispatch')
class TelegramBotWebhookView(View):
    def post(self, request, *args, **kwargs):
        try:
            # Extract user IP address
            user_ip = request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR')

            # Parse incoming JSON from Telegram
            json_str = request.body.decode('UTF-8')
            update = telebot.types.Update.de_json(json.loads(json_str))
            
            # Get the user's country
            user_country = get_user_country(user_ip)
            
            # Apply Malaysia-specific or global logic
            if user_country == "Malaysia":
                return self.handle_malaysia(update)
            else:
                return self.handle_other_countries(update)
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=200)

    def handle_malaysia(self, update):
        """Block users from Malaysia."""
        app.send_message(update.message.chat.id, "הרובוט הזה מיועד לבני אדם בלבד... ציונים אינם יכולים להשתמש בו!")
        return JsonResponse({"status": "success", "message": "Handled for Malaysia"})

    def handle_other_countries(self, update):
        """Handle requests from users outside Malaysia."""
        app.send_message(update.message.chat.id, "به ربات ما خوش آمدید!")
        return JsonResponse({"status": "success", "message": "Handled for other countries"})

# Helper function: Check subscription
def check_subscription(user, channels=my_channels_with_atsign):
    for channel in channels:
        is_member = app.get_chat_member(chat_id=channel, user_id=user)
        if is_member.status in ["kicked", "left"]:
            return False
    return True

# Start command handler
@app.message_handler(commands=['start'])
def start(message):
    # User Info
    tel_id = message.from_user.username if message.from_user.username else message.from_user.id
    tel_name = message.from_user.first_name

    # Make a POST request to the registration API
    response = requests.post(f"{current_site}/api/check-registration/", json={"tel_id": tel_id})

    # Markup keyboards
    channel_markup = InlineKeyboardMarkup()
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
        )
    else:
        app.send_message(
            message.chat.id,
            f"{tel_name}\n عزیز شما قبلا در ربات کتونی اوریجینال ثبت نام کردید.\n\n"
        )

    # Check subscription status
    try:
        is_member = check_subscription(user=message.from_user.id)
        if not is_member:
            app.send_message(
                message.chat.id,
                "متاسفانه شما در کانال یا گروه ما عضو نیستید...\n\n برای استفاده از ربات در گروه و کانال زیر عضو شوید.",
                reply_markup=channel_markup
            )
    except Exception as e:
        logger.error(f"Error checking subscription: {e}")

@app.callback_query_handler(func=lambda call: call.data == 'check_subscription')
def handle_check_subscription(call):
    is_member = check_subscription(user=call.from_user.id)
    if is_member:
        app.answer_callback_query(call.id, "تشکر! عضویت شما تایید شد.")
        app.send_message(call.message.chat.id, "🎉 عضویت شما تایید شد. حالا می‌توانید از امکانات ربات استفاده کنید.")
    else:
        app.answer_callback_query(call.id, "لطفاً ابتدا در کانال یا گروه عضو شوید.")