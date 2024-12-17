# General imports
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
from .models import telbotid

# Variables imports
from utils.variables.TOKEN import TOKEN
from utils.variables.CHANNELS import my_channels_with_atsign, my_channels_without_atsign
from utils.telbot.functions import *
from utils.telbot.variables import main_menu, extra_buttons, retun_menue

###############################################################################################

# Logging setup
logger = logging.getLogger(__name__)

# App setup
app = TeleBot(token=TOKEN)
current_site = get_current_site()

# Tracking user menu history
user_sessions = defaultdict(lambda: {"history": [], "current_menu": None})

################################################################################################

# Webhook settings
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

# Helper function to send menu
def send_menu(chat_id, options, current_menu, extra_buttons=None):
    """Send a menu with options and update the session."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    # Organize buttons into rows of three
    rows = [options[i:i + 3] for i in range(0, len(options), 3)]
    for row in rows:
        markup.row(*row)

    # Add extra buttons
    if extra_buttons:
        extra_rows = [extra_buttons[i:i + 2] for i in range(0, len(extra_buttons), 2)]
        for extra_row in extra_rows:
            markup.row(*extra_row)

    # Update session: push current menu into history
    session = user_sessions[chat_id]
    if session["current_menu"] != current_menu:
        session["history"].append(session["current_menu"])
    session["current_menu"] = current_menu

    # Send the menu
    app.send_message(chat_id, "لطفاً یکی از گزینه‌ها را انتخاب کنید:", reply_markup=markup)

####################################################################################################

# Start handler
@app.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    tel_id = message.from_user.username if message.from_user.username else message.from_user.id
    tel_name = message.from_user.first_name
    response = requests.post(f"{current_site}/api/check-registration/", json={"tel_id": tel_id})

    if response.status_code == 201:
        app.send_message(
            message.chat.id,
            f"🏆 {tel_name} عزیز ثبت نامت با موفقیت انجام شد.\n\n",
        )
    else:
        app.send_message(
            message.chat.id,
            f"{tel_name} عزیز شما قبلا در ربات ثبت نام کرده‌اید.",
        )
    send_menu(chat_id, main_menu, "main_menu", extra_buttons)

#####################################################################################################

# Back Button Handler
@app.message_handler(func=lambda message: message.text == "🔙")
def handle_back(message):
    chat_id = message.chat.id
    session = user_sessions[chat_id]

    if session["history"]:
        previous_menu = session["history"].pop()
        session["current_menu"] = previous_menu

        # Handle back navigation
        if previous_menu == "main_menu":
            send_menu(chat_id, main_menu, "main_menu", extra_buttons)
        elif previous_menu.startswith("subcategory"):
            parent_category = previous_menu.split(":")[1]
            subcategories = {
                "پوشاک": ["ورزشی", "کت و شلوار", "زمستانه", "کفش و کتونی", "تابستانه"],
                "خوراکی": ["خشکبار", "خوار و بار", "سوپر مارکت"],
                "دیجیتال": ["لپتاب", "گوشی"],
            }
            send_menu(chat_id, subcategories[parent_category], previous_menu, retun_menue)
        elif previous_menu.startswith("products"):
            options = ["پر فروش ترین ها", "گران ترین ها", "ارزان ترین ها", "پر تخفیف ها"]
            send_menu(chat_id, options, previous_menu, retun_menue)
    else:
        session["current_menu"] = "main_menu"
        send_menu(chat_id, main_menu, "main_menu", extra_buttons)
        app.send_message(chat_id, "شما در منوی اصلی هستید.")

#####################################################################################################

# Subcategories Handler
@app.message_handler(func=lambda message: message.text in ["پوشاک", "خوراکی", "دیجیتال"])
def handle_subcategories(message):
    chat_id = message.chat.id
    parent_category = message.text
    subcategories = {
        "پوشاک": ["ورزشی", "کت و شلوار", "زمستانه", "کفش و کتونی", "تابستانه"],
        "خوراکی": ["خشکبار", "خوار و بار", "سوپر مارکت"],
        "دیجیتال": ["لپتاب", "گوشی"],
    }

    user_sessions[chat_id]["history"].append(user_sessions[chat_id]["current_menu"])
    user_sessions[chat_id]["current_menu"] = f"subcategory:{parent_category}"

    send_menu(chat_id, subcategories[parent_category], f"subcategory:{parent_category}", retun_menue)

# Products Handler
@app.message_handler(func=lambda message: message.text in [
    "ورزشی", "کت و شلوار", "زمستانه", "کفش و کتونی", "تابستانه", 
    "خشکبار", "خوار و بار", "سوپر مارکت", "لپتاب", "گوشی"
])
def handle_products(message):
    chat_id = message.chat.id
    subcategory = message.text
    options = ["پر فروش ترین ها", "گران ترین ها", "ارزان ترین ها", "پر تخفیف ها"]

    user_sessions[chat_id]["history"].append(user_sessions[chat_id]["current_menu"])
    user_sessions[chat_id]["current_menu"] = f"products:{subcategory}"

    send_menu(chat_id, options, f"products:{subcategory}", retun_menue)

#####################################################################################################

# Handle invalid commands
@app.message_handler(func=lambda message: True)
def handle_invalid(message):
    app.send_message(message.chat.id, "دستور نامعتبر است. لطفاً یکی از گزینه‌های منو را انتخاب کنید.")

#####################################################################################################

# Start polling (if used instead of webhook)
if __name__ == "__main__":
    app.polling()
