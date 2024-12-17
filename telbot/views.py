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
def send_menu(chat_id, options, current_menu, extra_buttons=None):
    """Send a menu with options and track user's current menu."""

    # Create the keyboard markup
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    # Organize buttons into rows of three
    rows = [options[i:i + 3] for i in range(0, len(options), 3)]
    for row in rows:
        markup.row(*row)

    # Add extra buttons like "بازدید سایت" or "منو اصلی"
    if extra_buttons:
        extra_rows = [extra_buttons[i:i + 2] for i in range(0, len(extra_buttons), 2)]
        for extra_row in extra_rows:
            markup.row(*extra_row)

    # Save the current menu in the user's history
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
        send_menu(message.chat.id, main_menu, "main_menu", extra_buttons)
    except Exception as e:
        app.send_message(message.chat.id, f"error is: {e}")
    


#####################################################################################################

# Handle messages
@app.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    text = message.text

    # Main menu
    if text == "🏡":
        send_menu(chat_id, main_menu, "main_menu", extra_buttons)
        user_menu_stack[chat_id] = []
        

    # Back to previous menu
    elif text == "🔙":
        if len(user_menu_stack[chat_id]) > 1:
            app.send_message(chat_id, f"Navigating back to: {user_menu_stack[chat_id]}")
            user_menu_stack[chat_id].pop()
            previous_menu = user_menu_stack[chat_id][-1]

            # Debugging information (optional)
            app.send_message(chat_id, f"Navigating back to: {user_menu_stack[chat_id]}")

            # Handle previous menu logic
            if previous_menu == "categories":
                show_categories(message)
            elif previous_menu in ["پوشاک", "خوراکی", "دیجیتال"]:
                # Return to the saved subcategory menu
                handle_category_name = previous_menu  # Name of the subcategory
                subcategories = {
                    "پوشاک": ["ورزشی", "کت و شلوار", "زمستانه", "کفش و کتونی", "تابستانه"],
                    "خوراکی": ["خشکبار", "خوار و بار", "سوپر مارکت"],
                    "دیجیتال": ["لپتاب", "گوشی"],
                }
                send_menu(chat_id, subcategories[handle_category_name], "subcategory", retun_menue)
            
        else:
            user_menu_stack[chat_id] = []  # Reset stack
            send_menu(chat_id, main_menu, "main_menu", extra_buttons)
            app.send_message(chat_id, "شما در منوی اصلی هستید.")



    # Specific actions for each button
    elif text == "موجودی":
        options = ["موجودی من", "افزایش موجودی"]
        home_menue = ["🏡"]
        send_menu(chat_id, options, "balance_category", home_menue)
        
    elif text == "موجودی من":
        show_balance(message)
        

    elif text == "خرید با کد کالا":
        ask_for_product_code(chat_id)

    elif text == "بازدید سایت":
        send_website_link(chat_id)

    # Categories
    elif text == "دسته بندی ها":
        options = ["پوشاک", "خوراکی", "دیجیتال"]
        home_menue = ["🏡"]
        send_menu(chat_id, options, "categories", home_menue)

    # Subcategories
    elif text in ["پوشاک", "خوراکی", "دیجیتال"]:
        subcategories = {
            "پوشاک": ["ورزشی", "کت و شلوار", "زمستانه", "کفش و کتونی", "تابستانه"],
            "خوراکی": ["خشکبار", "خوار و بار", "سوپر مارکت"],
            "دیجیتال": ["لپتاب", "گوشی"],
        }
        send_menu(chat_id, subcategories[text], "subcategory", retun_menue)


    # Products
    elif text in ["ورزشی", "کت و شلوار", "زمستانه", "کفش و کتونی", "تابستانه", "خشکبار", "خوار و بار", "سوپر مارکت", "لپتاب", "گوشی"]:
        # if text in ["ورزشی", "کت و شلوار", "زمستانه", "کفش و کتونی", "تابستانه"]:
            # user_menu_stack[chat_id].append('پوشاک')
        # elif text in ["خشکبار", "خوار و بار", "سوپر مارکت"]:
            # user_menu_stack[chat_id].append('خوراکی')
        # elif text in ["لپتاب", "گوشی"]:
            # user_menu_stack[chat_id].append('دیجیتال')
          # Save the subcategory name in the stack
        options = ["پر فروش ترین ها", "گران ترین ها", "ارزان ترین ها", "پر تخفیف ها"]
        send_menu(chat_id, options, user_menu_stack[chat_id][-1], retun_menue)

    else:
        app.send_message(chat_id, "دستور نامعتبر است. لطفاً یکی از گزینه‌های منو را انتخاب کنید.")


#####################################################################################################


# Functions for specific actions
def show_balance(message):
    # Example: Fetch and send user balance

    user_id = message.from_user.username
    balance = telbotid.objects.get(tel_id=user_id).credit
    formatted_balance = "{:,.2f}".format(float(balance))
    app.send_message(message.chat.id, f"موجودی شما: {formatted_balance} تومان") 

def ask_for_product_code(chat_id):
    app.send_message(chat_id, "لطفاً کد کالای مورد نظر را وارد کنید:")

@app.message_handler(func=lambda message: message.text.isdigit())
def handle_product_code(message):
    chat_id = message.chat.id
    product_code = message.text
    # Simulate a product lookup or API call
    app.send_message(chat_id, f"کالای با کد {product_code} ثبت شد.")

def send_website_link(chat_id):
    """Send a button that opens the website in a browser."""
    
    # Create an Inline Keyboard with a button linking to the website
    markup = types.InlineKeyboardMarkup()
    website_button = types.InlineKeyboardButton("بازدید از سایت", url=current_site)
    markup.add(website_button)

    # Send a message with the inline keyboard
    app.send_message(
        chat_id,
        "برای بازدید از سایت، دکمه زیر را فشار دهید:",
        reply_markup=markup
    )

def show_product_options(message):
    options = ["پر فروش ترین ها", "گران ترین ها", "ارزان ترین ها", "پر تخفیف ها"]
    send_menu(message.chat.id, options, "products", retun_menue)



# Categories handler
def show_categories(message):
    options = ["پوشاک", "خوراکی", "دیجیتال"]
    home_menue = ["🏡"]
    send_menu(message.chat.id, options, "categories", home_menue)

# Handle category
def handle_category(message):
    subcategories = {
        "پوشاک": ["ورزشی", "کت و شلوار", "زمستانه", "کفش و کتونی", "تابستانه"],
        "خوراکی": ["خشکبار", "خوار و بار", "سوپر مارکت"],
        "دیجیتال": ["لپتاب", "گوشی"],
    }
    send_menu(message.chat.id, subcategories[message.text], "subcategory", retun_menue)