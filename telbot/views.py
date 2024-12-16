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

# Logging setup
logger = logging.getLogger(__name__)

# App setup
app = TeleBot(token=TOKEN)
current_site = get_current_site()

# Tracking user menu history
user_menu_stack = defaultdict(list)

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

# Helper function to send menu
def send_menu(chat_id, options, current_menu, extra_buttons=None):
    """Send a menu with options and track user's current menu."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for option in options:
        markup.add(option)

    # Add extra buttons like "بازدید سایت" or "منو اصلی"
    if extra_buttons:
        for button in extra_buttons:
            markup.add(button)

    # Save the current menu in the user's history
    user_menu_stack[chat_id].append(current_menu)

    # Send the menu
    app.send_message(chat_id, "لطفاً یکی از گزینه‌ها را انتخاب کنید:", reply_markup=markup)

# Start handler
@app.message_handler(commands=['start'])
def start(message):
    tel_id = message.from_user.username if message.from_user.username else message.from_user.id
    tel_name = message.from_user.first_name
    response = requests.post(f"{current_site}/api/check-registration/", json={"tel_id": tel_id})

    # Define main menu
    main_menu = ["موجودی من", "خرید با کد کالا", "دسته بندی ها"]
    extra_buttons = ["بازدید سایت"]

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
    try:
        send_menu(message.chat.id, main_menu, "main_menu", extra_buttons)
    except Exception as e:
        app.send_message(message.chat.id, f"error is: {e}")
    

# Handle messages
@app.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    text = message.text

    # Main menu
    if text == "منو اصلی":
        user_menu_stack[chat_id] = []
        main_menu = ["موجودی من", "خرید با کد کالا", "دسته بندی ها"]
        extra_buttons = ["بازدید سایت"]
        send_menu(chat_id, main_menu, "main_menu", extra_buttons)

    # Back to previous menu
    elif text == "بازگشت به منو قبلی":
        if len(user_menu_stack[chat_id]) > 1:
            user_menu_stack[chat_id].pop()
            previous_menu = user_menu_stack[chat_id][-1]

            # Handle previous menu
            if previous_menu == "categories":
                show_categories(message)
            elif previous_menu == "subcategory":
                handle_category(message)
        else:
            app.send_message(chat_id, "شما در منوی اصلی هستید.")

    # Specific actions for each button
    elif text == "موجودی من":
        show_balance(chat_id)

    elif text == "خرید با کد کالا":
        ask_for_product_code(chat_id)

    elif text == "بازدید سایت":
        send_website_link(chat_id)

    # Categories
    elif text == "دسته بندی ها":
        options = ["پوشاک", "خوراکی", "دیجیتال", "بازگشت به منو قبلی"]
        send_menu(chat_id, options, "categories")

    # Subcategories
    elif text in ["پوشاک", "خوراکی", "دیجیتال"]:
        subcategories = {
            "پوشاک": ["ورزشی", "کت و شلوار", "زمستانه", "کفش و کتونی", "تابستانه", "بازگشت به منو قبلی"],
            "خوراکی": ["خشکبار", "خوار و بار", "سوپر مارکت", "بازگشت به منو قبلی"],
            "دیجیتال": ["لپتاب", "گوشی", "بازگشت به منو قبلی"],
        }
        send_menu(chat_id, subcategories[text], "subcategory")

    # Products
    elif text in ["ورزشی", "کت و شلوار", "زمستانه", "کفش و کتونی", "تابستانه", "خشکبار", "خوار و بار", "سوپر مارکت", "لپتاب", "گوشی"]:
        show_product_options(chat_id)

    else:
        app.send_message(chat_id, "دستور نامعتبر است. لطفاً یکی از گزینه‌های منو را انتخاب کنید.")

# Functions for specific actions
def show_balance(chat_id):
    # Example: Fetch and send user balance
    user_id = "HusseinMohammadi2079"
    balance = telbotid.objects.get(tel_id=user_id).credit
    formatted_balance = "{:,.2f}".format(float(balance))
    
    app.send_message(chat_id, f"موجودی شما: {formatted_balance} تومان") 

def ask_for_product_code(chat_id):
    app.send_message(chat_id, "لطفاً کد کالای مورد نظر را وارد کنید:")

@app.message_handler(func=lambda message: message.text.isdigit())
def handle_product_code(message):
    chat_id = message.chat.id
    product_code = message.text
    # Simulate a product lookup or API call
    app.send_message(chat_id, f"کالای با کد {product_code} ثبت شد.")

def send_website_link(chat_id):
    website_url = f"https://{current_site}/"
    app.send_message(chat_id, f"برای بازدید از سایت روی لینک زیر کلیک کنید:\n{website_url}")

def show_product_options(chat_id):
    options = ["پر فروش ترین ها", "گران ترین ها", "ارزان ترین ها", "پر تخفیف ها", "بازگشت به منو قبلی"]
    send_menu(chat_id, options, "products")



# Categories handler
def show_categories(message):
    options = ["پوشاک", "خوراکی", "دیجیتال", "بازگشت به منو قبلی"]
    send_menu(message.chat.id, options, "categories")

# Handle category
def handle_category(message):
    subcategories = {
        "پوشاک": ["ورزشی", "کت و شلوار", "زمستانه", "کفش و کتونی", "تابستانه", "بازگشت به منو قبلی"],
        "خوراکی": ["خشکبار", "خوار و بار", "سوپر مارکت", "بازگشت به منو قبلی"],
        "دیجیتال": ["لپتاب", "گوشی", "بازگشت به منو قبلی"],
    }
    send_menu(message.chat.id, subcategories[message.text], "subcategory")