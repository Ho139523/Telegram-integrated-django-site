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
def send_menu(message, options, current_menu, extra_buttons=None):
    """Send a menu with options and update the session."""
    try:
        if check_subscription(user=message.from_user.id)==False:
            app.send_message(message.chat.id, "برای تایید عضویت خود در گروه و کانال بر روی دکمه‌ها کلیک کنید.", reply_markup=channel_markup)
            
        else:
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
            session = user_sessions[message.chat.id]
            if session["current_menu"] != current_menu:
                session["history"].append(session["current_menu"])
            session["current_menu"] = current_menu

            # Send the menu
            app.send_message(message.chat.id, "لطفاً یکی از گزینه‌ها را انتخاب کنید:", reply_markup=markup)
            app.send_message(message.chat.id, f"the history is : {session["history"]}")
        
    except Exception as e:
        app.send_message(message.chat.id, f"the error is : {e}")



# Check subscription
def check_subscription(user, channels=my_channels_with_atsign):
    for channel in channels:
        is_member = app.get_chat_member(chat_id=channel, user_id=user)
        if is_member.status in ["kicked", "left"]:
            return False
        return True



# subscription offer
def subscription_offer(message):
    # Create keyboard for subscription check
        channel_markup = types.InlineKeyboardMarkup()
        current_site_markup = types.InlineKeyboardMarkup(row_width=1)
        current_site_button = types.InlineKeyboardButton(text='بازدید از سایت', url=f"{current_site}")
        check_subscription_button = types.InlineKeyboardButton(text='عضو شدم.', callback_data='check_subscription')
        channel_subscription_button = types.InlineKeyboardButton(text='در کانال ما عضو شوید...', url=f"https://t.me/{my_channels_without_atsign[0]}")
        group_subscription_button = types.InlineKeyboardButton(text="در گروه ما عضو شوید...", url=f"https://t.me/{my_channels_without_atsign[1]}")
        
        channel_markup.add(channel_subscription_button, group_subscription_button)
        channel_markup.add(check_subscription_button)
        current_site_markup.add(current_site_button)
        
        if check_subscription(user=message.from_user.id)==False:
            app.send_message(message.chat.id, "برای تایید عضویت خود در گروه و کانال بر روی دکمه‌ها کلیک کنید.", reply_markup=channel_markup)
            return False
        else:
            return True


####################################################################################################


# Start handler
@app.message_handler(commands=['start'])
def start(message):
    try:
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
         
        
        if subscription_offer(message):
            # Display the main menu
            # Reset session
            user_sessions[message.chat.id] = {"history": [], "current_menu": None}
            send_menu(message.chat.id, main_menu, "main_menu", extra_buttons)
            
            
        
    except Exception as e:
        app.send_message(message.chat.id, f"the error is : {e}")
    


#####################################################################################################


@app.callback_query_handler(func=lambda call: call.data == 'check_subscription')
def handle_check_subscription(call):
    user_id = call.from_user.id
    is_member = check_subscription(user_id)
    
    if is_member:
        app.answer_callback_query(call.id, "تشکر! عضویت شما تایید شد.")
        app.edit_message_text("🎉 عضویت شما تایید شد. حالا می‌توانید از امکانات ربات استفاده کنید.",
                              chat_id=call.message.chat.id, message_id=call.message.message_id)
        
        # Display the main menu
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("موجودی من", "خرید با کد کالا", "دسته بندی ها", "منو اصلی")
        app.send_message(call.message.chat.id, "انتخاب کنید:", reply_markup=markup)
    else:
        app.answer_callback_query(call.id, "لطفاً ابتدا در کانال یا گروه عضو شوید.")


# Back to Previous Menu
# @app.message_handler(func=lambda message: message.text == "🔙")
# def handle_back(message):
    # chat_id = message.chat.id
    # session = user_sessions[chat_id]

    # if session["history"]:
        # previous_menu = session["history"].pop()
        # session["current_menu"] = previous_menu

        # # Handle back navigation
        # if previous_menu == "main_menu":
            # send_menu(message, main_menu, "main_menu", extra_buttons)
        # elif previous_menu.startswith("subcategory"):
            # parent_category = previous_menu.split(":")[1]
            # subcategories = {
                # "پوشاک": ["ورزشی", "کت و شلوار", "زمستانه", "کفش و کتونی", "تابستانه"],
                # "خوراکی": ["خشکبار", "خوار و بار", "سوپر مارکت"],
                # "دیجیتال": ["لپتاب", "گوشی"],
            # }
            # send_menu(message, subcategories[parent_category], f"subcategory:{parent_category}", retun_menue)
        # elif previous_menu.startswith("products"):
            # options = ["پر فروش ترین ها", "گران ترین ها", "ارزان ترین ها", "پر تخفیف ها"]
            # send_menu(message, options, "products", retun_menue)
    # else:
        # # If no history, return to main menu
        # session["current_menu"] = "main_menu"
        # send_menu(message, main_menu, "main_menu", extra_buttons)
        # app.send_message(chat_id, "شما در منوی اصلی هستید.")



# Handle messages
@app.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    text = message.text

    # Main menu
    if text == "🏡":
        user_sessions = defaultdict(lambda: {"history": [], "current_menu": None})
        
        send_menu(message, main_menu, "main_menu", extra_buttons)

    # Back to previous menu
   


    # Specific actions for each button
    elif text == "موجودی":
        options = ["موجودی من", "افزایش موجودی"]
        home_menue = ["🏡"]
        send_menu(message, options, "balance_category", home_menue)
        
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
        send_menu(message, options, "categories", home_menue)

    # Subcategories
    elif text in ["پوشاک", "خوراکی", "دیجیتال"]:
        subcategories = {
            "پوشاک": ["ورزشی", "کت و شلوار", "زمستانه", "کفش و کتونی", "تابستانه"],
            "خوراکی": ["خشکبار", "خوار و بار", "سوپر مارکت"],
            "دیجیتال": ["لپتاب", "گوشی"],
        }
        send_menu(message, subcategories[text], "subcategory", retun_menue)


    # Products
    elif text in ["ورزشی", "کت و شلوار", "زمستانه", "کفش و کتونی", "تابستانه", "خشکبار", "خوار و بار", "سوپر مارکت", "لپتاب", "گوشی"]:
        options = ["پر فروش ترین ها", "گران ترین ها", "ارزان ترین ها", "پر تخفیف ها"]
        send_menu(message, options, "products", retun_menue)

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
    send_menu(message, options, "products", retun_menue)



# Categories handler
def show_categories(message):
    options = ["پوشاک", "خوراکی", "دیجیتال"]
    home_menue = ["🏡"]
    send_menu(message, options, "categories", home_menue)

# Handle category
def handle_category(message):
    subcategories = {
        "پوشاک": ["ورزشی", "کت و شلوار", "زمستانه", "کفش و کتونی", "تابستانه"],
        "خوراکی": ["خشکبار", "خوار و بار", "سوپر مارکت"],
        "دیجیتال": ["لپتاب", "گوشی"],
    }
    send_menu(message, subcategories[message.text], "subcategory", retun_menue)
    
    
# Subcategories Handler
@app.message_handler(func=lambda message: message.text in ["پوشاک", "خوراکی", "دیجیتال"])
def handle_subcategories(message):
    chat_id = message.chat.id
    parent_category = message.text  # Save the parent category
    subcategories = {
        "پوشاک": ["ورزشی", "کت و شلوار", "زمستانه", "کفش و کتونی", "تابستانه"],
        "خوراکی": ["خشکبار", "خوار و بار", "سوپر مارکت"],
        "دیجیتال": ["لپتاب", "گوشی"],
    }

    # Save session
    user_sessions[chat_id]["history"].append(user_sessions[chat_id]["current_menu"])
    user_sessions[chat_id]["current_menu"] = f"subcategory:{parent_category}"

    # Send subcategory menu
    send_menu(message, subcategories[parent_category], "subcategory", retun_menue)


# Products Handler
@app.message_handler(func=lambda message: message.text in [
    "ورزشی", "کت و شلوار", "زمستانه", "کفش و کتونی", "تابستانه", 
    "خشکبار", "خوار و بار", "سوپر مارکت", "لپتاب", "گوشی"
])
def handle_products(message):
    chat_id = message.chat.id
    subcategory = message.text  # Save subcategory
    options = ["پر فروش ترین ها", "گران ترین ها", "ارزان ترین ها", "پر تخفیف ها"]

    # Save session
    user_sessions[chat_id]["history"].append(user_sessions[chat_id]["current_menu"])
    user_sessions[chat_id]["current_menu"] = f"products:{subcategory}"

    # Send products menu
    send_menu(message, options, "products", retun_menue)
