# General imports
from telebot import TeleBot, types
from collections import defaultdict
import requests
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
from utils.telbot.variables import main_menu

###############################################################################################

# Logging setup
logger = logging.getLogger(__name__)

# App setup
app = TeleBot(token=TOKEN)
current_site = get_current_site()

# Tracking user menu history
user_menu_stack = defaultdict(list)

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
def send_menu(chat_id, options, current_menu, extra_buttons=None, is_submenu=False):
    """
    Send a menu with options.
    - Adds dynamic row widths for buttons.
    - Submenus exclude "منو اصلی" button and have specific row arrangements.
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    # Define row width dynamically
    row_width = 3 if not is_submenu else 1
    rows = [options[i:i + row_width] for i in range(0, len(options), row_width)]

    # Add main options with row width
    for row in rows:
        markup.row(*row)

    # Add back and main menu buttons at the bottom
    if current_menu == "main_menu":
        markup.row("بازگشت به منو قبلی", "منو اصلی")
    else:
        # Only "بازگشت به منو قبلی" for submenus
        markup.row("بازگشت به منو قبلی")

    # Save current menu to user's history
    user_menu_stack[chat_id].append(current_menu)

    # Send the menu
    app.send_message(chat_id, "لطفاً یکی از گزینه‌ها را انتخاب کنید:", reply_markup=markup)


####################################################################################################


# Start handler
@app.message_handler(commands=['start'])
def start(message):
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
    try:
        send_menu(message.chat.id, main_menu, "main_menu")
    except Exception as e:
        app.send_message(message.chat.id, f"error is: {e}")


#####################################################################################################

# Handle messages
@app.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    text = message.text

    # Main menu
    if text == "منو اصلی":
        user_menu_stack[chat_id] = []  # Reset menu history
        send_menu(chat_id, main_menu, "main_menu")

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
    elif text == "موجودی":
        options = ["موجودی من", "افزایش موجودی"]
        send_menu(chat_id, options, "balance_category", is_submenu=True)

    elif text == "خرید با کد کالا":
        ask_for_product_code(chat_id)

    elif text == "بازدید سایت":
        send_website_link(chat_id)

    # Categories
    elif text == "دسته بندی ها":
        options = ["پوشاک", "خوراکی", "دیجیتال"]
        send_menu(chat_id, options, "categories", is_submenu=True)

    # Subcategories
    elif text in ["پوشاک", "خوراکی", "دیجیتال"]:
        subcategories = {
            "پوشاک": ["ورزشی", "کت و شلوار", "زمستانه", "کفش و کتونی", "تابستانه"],
            "خوراکی": ["خشکبار", "خوار و بار", "سوپر مارکت"],
            "دیجیتال": ["لپتاب", "گوشی"],
        }
        send_menu(chat_id, subcategories[text], "subcategory", is_submenu=True)

    # Products
    elif text in ["ورزشی", "کت و شلوار", "زمستانه", "کفش و کتونی", "تابستانه", "خشکبار", "خوار و بار", "سوپر مارکت", "لپتاب", "گوشی"]:
        show_product_options(chat_id)

    else:
        app.send_message(chat_id, "دستور نامعتبر است. لطفاً یکی از گزینه‌های منو را انتخاب کنید.")


#####################################################################################################

# Functions for specific actions
def ask_for_product_code(chat_id):
    app.send_message(chat_id, "لطفاً کد کالای مورد نظر را وارد کنید:")


@app.message_handler(func=lambda message: message.text.isdigit())
def handle_product_code(message):
    chat_id = message.chat.id
    product_code = message.text
    app.send_message(chat_id, f"کالای با کد {product_code} ثبت شد.")


def send_website_link(chat_id):
    """Send a button that opens the website in a browser."""
    markup = types.InlineKeyboardMarkup()
    website_button = types.InlineKeyboardButton("بازدید از سایت", url=str(current_site))
    markup.add(website_button)

    app.send_message(
        chat_id,
        "برای بازدید از سایت، دکمه زیر را فشار دهید:",
        reply_markup=markup
    )


def show_product_options(chat_id):
    options = ["پر فروش ترین ها", "گران ترین ها", "ارزان ترین ها", "پر تخفیف ها"]
    send_menu(chat_id, options, "products", is_submenu=True)


def show_categories(message):
    options = ["پوشاک", "خوراکی", "دیجیتال"]
    send_menu(message.chat.id, options, "categories", is_submenu=True)


def handle_category(message):
    subcategories = {
        "پوشاک": ["ورزشی", "کت و شلوار", "زمستانه", "کفش و کتونی", "تابستانه"],
        "خوراکی": ["خشکبار", "خوار و بار", "سوپر مارکت"],
        "دیجیتال": ["لپتاب", "گوشی"],
    }
    send_menu(message.chat.id, subcategories[message.text], "subcategory", is_submenu=True)
