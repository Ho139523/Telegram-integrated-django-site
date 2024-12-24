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
from django.utils.html import format_html


# support imports
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup
from telebot import custom_filters

# Variables imports
from utils.variables.TOKEN import TOKEN
from utils.variables.CHANNELS import my_channels_with_atsign, my_channels_without_atsign
from utils.telbot.functions import *
from utils.telbot.variables import main_menu, extra_buttons, retun_menue
import re
from bs4 import BeautifulSoup

# import models
from products.models import Category, Product
from telebot.types import Message


###############################################################################################

# Logging setup
logger = logging.getLogger(__name__)

# support memmory
state_storage = StateMemoryStorage()

# App setup
app = TeleBot(token=TOKEN, state_storage=state_storage)
current_site = 'https://intelleum.ir'

# Tracking user menu history
user_sessions = defaultdict(lambda: {"current_menu": None})

# support class
chat_ids=[]
texts={}
codes={}
class Support(StatesGroup):
    text = State()
    respond = State()
    code = State()
    
    
# model variables


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
    if subscription_offer(message):
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

        

        # Send the menu
        return markup


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


# Function to escape all special characters with a backslash
def escape_special_characters(text):
    special_characters = r"([\*\_\[\]\(\)\~\`\>\#\+\-\=\|\{\}\.\!])"
    return re.sub(special_characters, r'\\\1', text)

####################################################################################################


# Start handler
@app.message_handler(commands=['start'])
def start(message):
    try:
        tel_id = message.from_user.username if message.from_user.username else message.from_user.id
        tel_name = message.from_user.first_name
        response = requests.post(f"{current_site}/telbot/api/check-registration/", json={"tel_id": tel_id})

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
            
            markup = send_menu(message, main_menu, "main_menu", extra_buttons)
            app.send_message(message.chat.id, "لطفاً یکی از گزینه‌ها را انتخاب کنید:", reply_markup=markup)
        
    except Exception as e:
        app.send_message(message.chat.id, f"the error is: {e}")



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
@app.message_handler(func=lambda message: message.text == "🔙")
def handle_back(message):
    if subscription_offer(message):
        try:
            session = user_sessions[message.chat.id]
            
            # Get the previous category's title
            try:
                previous_category_title = Category.objects.get(
                    title__iexact=session["current_menu"], status=True
                ).get_parents()[0].title
                
                # Manually trigger the handler by simulating a message
                fake_message = message  # Clone the current message
                fake_message.text = previous_category_title  # Change the text to previous category
                
                # Call the subcategory handler directly
                subcategory(fake_message)
            
            except IndexError as e:
                if "list index out of range" in str(e):
                    previous_category_title = "دسته بندی ها"
                    
                    fake_message = message  # Clone the current message
                    fake_message.text = previous_category_title  # Change the text to previous category
                    
                    # Call the subcategory handler directly
                    category(fake_message)
             

            

        except Exception as e:
            app.send_message(message.chat.id, f"the error is: {e}")



# Home
@app.message_handler(func=lambda message: message.text=="🏡")
def home(message):
    if subscription_offer(message):
        user_sessions = defaultdict(lambda: {"history": [], "current_menu": None})
        markup = send_menu(message, main_menu, "main_menu", extra_buttons)
        app.send_message(message.chat.id, "لطفا یکی از گزینه های زیر را انتخاب کنید:", reply_markup=markup)
    

# Visit website
@app.message_handler(func=lambda message: message.text=="بازدید سایت")
def visit_website(message):
    if subscription_offer(message):
        send_website_link(message)
        app.send_message(message.chat.id, f"error is: {e}")
        
        
# balance
@app.message_handler(func=lambda message: message.text=="موجودی")
def balance_menue(message):
    if subscription_offer(message):
        options = ["موجودی من", "افزایش موجودی"]
        home_menue = ["🏡"]
        markup = send_menu(message, options, "balance_category", home_menue)
        app.send_message(message.chat.id, "می خوای موجودی بگیری یا موجودیت رو افزایش بدی؟", reply_markup=markup)
        
        
# show balance
@app.message_handler(func=lambda message: message.text=="موجودی من")
def my_balance(message):
    if subscription_offer(message):
        show_balance(message)
        
# Buy products with code
@app.message_handler(func=lambda message: message.text=="خرید با کد کالا")
def buy_with_code(message):
    if subscription_offer(message):
        ask_for_product_code(message)


# First Layer category
@app.message_handler(func=lambda message: message.text=="دسته بندی ها")
def category(message):
    if subscription_offer(message):
        cats = Category.objects.filter(parent__isnull=True, status=True).values_list('title', flat=True)
        home_menue = ["🏡"]
        markup = send_menu(message, cats, message.text, home_menue)
        app.send_message(message.chat.id, "کالایی که دنبالشی جزو کدام دسته است", reply_markup=markup)
        
        

# second layer category
@app.message_handler(func=lambda message: message.text in Category.objects.filter(title__iexact=message.text, status=True).values_list('title', flat=True))
def subcategory(message):
    try:
        if subscription_offer(message):
            current_category = Category.objects.get(title__iexact=message.text, status=True)
            
            # Get the titles of the child categories
            children = [child.title for child in current_category.get_next_layer_categories()]
            
            # Send full path of the category
            
            
            # Send the child titles to the menu
            if children == []:
                # Update session: push current menu into history
                session = user_sessions[message.chat.id]
                
                session["current_menu"] = message.text
                
                fake_message = message  # Clone the current message
                fake_message.text = "hi"
                handle_products(fake_message)
            else:
                # Update session: push current menu into history
                session = user_sessions[message.chat.id]
                
                session["current_menu"] = message.text
                markup = send_menu(message, children, message.text, retun_menue)
                app.send_message(message.chat.id, f"{current_category.get_full_path()}", reply_markup=markup)
            
    except Exception as e:
        print(f'Error: {e}')



# Top discounts
def handle_products(message):
    if subscription_offer(message):
        chat_id = message.chat.id
        subcategory = message.text  # Save subcategory
        options = ["پر فروش ترین ها", "گران ترین ها", "ارزان ترین ها", "پر تخفیف ها"]

        # Save session
        home_menue = ["🏡"]
        markup = send_menu(message, options, "products", home_menue)
        session = user_sessions[message.chat.id]
        current_category = Category.objects.get(title__iexact=session["current_menu"], status=True)
        app.send_message(message.chat.id, f"{current_category.get_full_path()}", reply_markup=markup)
        



# 10 products
@app.message_handler(func=lambda message: message.text in ["پر فروش ترین ها", "گران ترین ها", "ارزان ترین ها", "پر تخفیف ها"])
def handle_ten_products(message):
    if subscription_offer(message):
        if message.text == "پر تخفیف ها":
            products = Product.objects.filter(category__title=user_sessions[message.chat.id]["current_menu"]).order_by("discount")[:10]

        elif message.text=="پر فروش ترین ها":
            app.send_message(message.chat.id, f"با عرض پوزش هنوز این قابلیت فعال نشده است.")
            
        elif message.text=="ارزان ترین ها":
            products = Product.objects.filter(category__title=user_sessions[message.chat.id]["current_menu"]).order_by("-price")[:10]
            
        elif message.text=="گران ترین ها":
            products = Product.objects.filter(category__title=user_sessions[message.chat.id]["current_menu"]).order_by("price")[:10]
        
        if not products.exists():
                hhh=user_sessions[message.chat.id]['current_menu']
                app.send_message(message.chat.id, "محصولی در این دسته بندی یافت نشد.")
                return
        else:
            try:
                for product in products:
                    formatted_price = "{:,.0f}".format(float(product.price))
                    formatted_final_price = "{:,.0f}".format(float(product.final_price))
                    caption = format_html(
                        f"⭕️ {product.name}\n"
                        f"کد کالا: {product.code}\n\n"
                        f"{product.description}\n\n"
                        f"🔘 فروش با ضمانت ارویجینال💯\n"
                        f"📫 ارسال به تمام نقاط کشور\n"
                        f"🏃 {product.discount} % تخفیف\n"
                        f"💵 قیمت: <s>{formatted_price}</s> تومان ⬅ {formatted_final_price} تومان"
                    )
                    photos = [
                        types.InputMediaPhoto(open(product.main_image.path, 'rb'), caption=caption, parse_mode='HTML')
                    ] + [
                        types.InputMediaPhoto(open(i.image.path, 'rb')) for i in product.image_set.all()
                    ]
                    #app.send_message(message.chat.id, f"{print([i.image.path for i in product.additional_images.all()])}")

                    if len(photos) > 10:
                        photos = photos[:10]  # محدود به 10 عکس
                    
                    markup = types.InlineKeyboardMarkup()
                    buy_button = types.InlineKeyboardButton(text="خرید", url=f"{current_site}/bbuy/product/product_code")#, callback_data=f"buy_{product['code']}")
                    markup.add(buy_button)
                    app.send_media_group(message.chat.id, media=photos)
                    app.send_message(message.chat.id, "برای خریدن این محصول کلیک کنید 👇👇👇", reply_markup=markup)

            except Exception as e:
                app.send_message(message.chat.id, f"the error is: {e}")


##################################
# support handlers

# Handling the 'Support 👨🏻‍💻' button click event
@app.message_handler(func= lambda message: message.text == "پیام به پشتیبان")
def sup(message):
    app.send_message(chat_id=message.chat.id, text="لطفا پیام خود را تایپ کنید:")
    app.set_state(user_id=message.from_user.id, state=Support.text, chat_id=message.chat.id)    


# Handling the user's first message which is saved in 'Support.text' state
@app.message_handler(state=Support.text)
def sup_text(message):
    try:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="پاسخ", callback_data="پاسخ"))

        app.send_message(chat_id=5629898030, text=f"Recived a message from <code>{message.from_user.id}</code> with username @{message.from_user.username}:\n\nMessage text:\n<b>{escape_special_characters(message.text)}</b>", reply_markup=markup, parse_mode="HTML")

        app.send_message(chat_id=message.chat.id, text="Your message was sent!")

        texts[message.from_user.id] = message.text

        # app.delete_state(user_id=message.from_user.id, chat_id=message.chat.id)
    except Exception as e:
        app.send_message(chat_id=message.chat.id, text=f"the error is: {e}")
    
# Handling the support agent's reply message which is saved in 'Support.respond' state
@app.message_handler(state=Support.respond, func= lambda message: message.reply_to_message.text.startswith("Send your answer to"))
def answer_text(message):
    try:
        pattern = r"Send your answer to \d+"
        clean_text = BeautifulSoup(message.reply_to_message.text, "html.parser").get_text()
        user = int(re.findall(pattern=pattern, string=clean_text)[0].split()[4])

        try:
            user_message = texts[user]
            app.send_message(chat_id=user, text=f"Your message:\n<i>{escape_special_characters(user_message)}</i>\n\nSupport answer:\n<b>{escape_special_characters(message.text)}</b>", parse_mode="HTML")
            app.send_message(chat_id=message.chat.id, text="Your answer was sent!")

            del texts[user]
            app.delete_state(user_id=message.from_user.id, chat_id=message.chat.id)
        
        except:
            app.send_message(chat_id=user, text=f"Support answer:\n<b>{escape_special_characters(message.text)}</b>", parse_mode="HTML")
            app.send_message(chat_id=message.chat.id, text="Your answer was sent!")

            app.delete_state(user_id=message.from_user.id, chat_id=message.chat.id)
        
    except Exception as e:
        app.send_message(chat_id=message.chat.id, text=f"Something goes wrong...\n\nException:\n<code>{e}</code>", parse_mode="HTML")

    markup = send_menu(message, main_menu, "main_menu", extra_buttons)
    app.send_message(message.chat.id, "لطفا یکی از گزینه های زیر را انتخاب کنید:", reply_markup=markup)
##################################



@app.message_handler(state=Support.code)
def handle_product_code(message):
    if subscription_offer(message):
        chat_id = message.chat.id
        product_code = message.text
        if re.match(r'^[A-Z]{4}\d{6}$', message.text):
            app.send_message(chat_id, f"کالای با کد {product_code} ثبت شد.")
        else:
            app.send_message(chat_id, "قالب کدی که وارد کرده اید نادرست است. از صحت کد اطمینان حاصل کنید.")
    else:
        app.send_message(message.chat.id, "شما باید یک اشتراک فعال داشته باشید.")


# Handle messages
@app.message_handler(func=lambda message: True)
def handle_message(message):
    if subscription_offer(message):
        app.send_message(message.chat.id, "دستور نامعتبر است. لطفاً یکی از گزینه‌های منو را انتخاب کنید")


#####################################################################################################
# Functions for specific actions



# show balance
def show_balance(message):
    # Example: Fetch and send user balance
    if subscription_offer(message):
        user_id = message.from_user.username
        balance = telbotid.objects.get(tel_id=user_id).credit
        formatted_balance = "{:,.2f}".format(float(balance))
        app.send_message(message.chat.id, f"موجودی شما: {formatted_balance} تومان") 

def ask_for_product_code(message):
    if subscription_offer(message):
        app.send_message(message.chat.id, "لطفاً کد کالای مورد نظر را وارد کنید:")
        app.set_state(user_id=message.from_user.id, state=Support.code, chat_id=message.chat.id)  



def send_website_link(message):
    """Send a button that opens the website in a browser."""
    if subscription_offer(message):
        # Create an Inline Keyboard with a button linking to the website
        markup = types.InlineKeyboardMarkup()
        website_button = types.InlineKeyboardButton("بازدید از سایت", url=current_site)
        markup.add(website_button)

        # Send a message with the inline keyboard
        app.send_message(
            message.chat.id,
            "برای بازدید از سایت، دکمه زیر را فشار دهید:",
            reply_markup=markup
        )




##############################################################################################

        



# Handling the callback query when the 'answer' button is clicked
@app.callback_query_handler(func= lambda call: call.data == "پاسخ")
def answer(call):
    try:
        pattern = r"Recived a message from \d+"
        clean_text = BeautifulSoup(call.message.text, "html.parser").get_text()
        user = re.findall(pattern=pattern, string=clean_text)[0].split()[4]
        
        app.send_message(chat_id=call.message.chat.id, text=f"Send your answer to <code>{user}</code>:", reply_markup=types.ForceReply(), parse_mode="HTML")

        app.set_state(user_id=call.from_user.id, state=Support.respond, chat_id=call.message.chat.id)
    
    except Exception as e:
        app.send_message(chat_id=call.message.chat.id, text=f"the error is: {e}")



app.add_custom_filter(custom_filters.StateFilter(app))