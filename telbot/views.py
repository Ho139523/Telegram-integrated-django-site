# General imports
import re
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
from bs4 import BeautifulSoup

# import models
from products.models import Category, Product, ProductAttribute
from telbot.models import ConversationModel, MessageModel
from telebot.types import Message

# copy telegram text link
from django.shortcuts import render


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
from accounts.models import ProfileModel, ShippingAddressModel
from accounts.models import User
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode



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
@app.message_handler(func=lambda message: message.text.startswith("/start activate_"))
def handle_activation_account(message):
    try:
        parts = message.text.split('_')
        if len(parts) != 3:
            app.send_message(message.chat.id, "لینک فعالسازی نامعتبر است.")
            return

        _, uid, token = parts
        uid = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=uid)

        if generate_token.check_token(user, token):
            user.is_active = True
            user.save()

            # Create or get the profile
            profile, created = ProfileModel.objects.get_or_create(user=user)

            # Create a shipping address if it doesn't already exist
            if not hasattr(profile, 'shippingaddressmodel'):
                shippingaddress = ShippingAddressModel(profile=profile)
                shippingaddress.save()

            # Save the profile
            user.profilemodel.save()
            profile.save()

            # Send a confirmation message to the user
            app.send_message(message.chat.id, f"{message.from_user.first_name} عزیز حساب شما فعال شد.")

            # Optionally, you can also send a message like "Now, let's proceed with the address..." if needed.
            app.send_message(message.chat.id, "حالا بریم سراغ آدرس...")

        else:
            app.send_message(message.chat.id, "لینک فعالسازی نامعتبر است یا منقضی شده است.")
    except Exception as e:
        app.send_message(message.chat.id, f"خطا: {e}")  # Log error





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
        markup.add("💰 موجودی من", "خرید با کد کالا", "🗂 دسته بندی ها", "منو اصلی")
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
                    previous_category_title = "🗂 دسته بندی ها"
                    
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
@app.message_handler(func=lambda message: message.text=="🖥 بازدید سایت")
def visit_website(message):
    if subscription_offer(message):
        send_website_link(message)
        app.send_message(message.chat.id, f"error is: {e}")
        
        
# balance
@app.message_handler(func=lambda message: message.text=="🧮 موجودی")
def balance_menue(message):
    if subscription_offer(message):
        options = ["💰 موجودی من", "💳 افزایش موجودی"]
        home_menue = ["🏡"]
        markup = send_menu(message, options, "balance_category", home_menue)
        app.send_message(message.chat.id, "می خوای موجودی بگیری یا موجودیت رو افزایش بدی؟", reply_markup=markup)
        
        
# show balance
@app.message_handler(func=lambda message: message.text=="💰 موجودی من")
def my_balance(message):
    if subscription_offer(message):
        show_balance(message)
        
# Buy products with code
@app.message_handler(func=lambda message: message.text=="خرید با کد کالا")
def buy_with_code(message):
    if subscription_offer(message):
        ask_for_product_code(message)


# First Layer category
@app.message_handler(func=lambda message: message.text=="🗂 دسته بندی ها")
def category(message):
    if subscription_offer(message):
        cats = Category.objects.filter(parent__isnull=True, status=True).values_list('title', flat=True)
        home_menue = ["🏡"]
        markup = send_menu(message, cats, message.text, home_menue)
        app.send_message(message.chat.id, "کالایی که دنبالشی جزو کدام دسته است", reply_markup=markup)
        
        

# second layer category
@app.message_handler(func=lambda message: message.text.title() in Category.objects.filter(title__iexact=message.text, status=True).values_list('title', flat=True))
def subcategory(message):
    try:
        if subscription_offer(message):
            current_category = Category.objects.get(title__iexact=message.text.title(), status=True)
            
            # Get the titles of the child categories
            children = [child.title for child in current_category.get_next_layer_categories()]
            
            # Send full path of the category
            
            
            # Send the child titles to the menu
            if children == []:
                # Update session: push current menu into history
                session = user_sessions[message.chat.id]
                
                session["current_menu"] = message.text.title()
                
                fake_message = message  # Clone the current message
                fake_message.text = "hi"
                handle_products(fake_message)
            else:
                # Update session: push current menu into history
                session = user_sessions[message.chat.id]
                
                session["current_menu"] = message.text.title()
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
            if Product.objects.filter(category__title=user_sessions[message.chat.id]["current_menu"], discount__gt=0).exists():
                products = Product.objects.filter(category__title=user_sessions[message.chat.id]["current_menu"], discount__gt=0).order_by("discount")[:10]
            else:
                products = []

        elif message.text=="پر فروش ترین ها":
            app.send_message(message.chat.id, f"🚧 با عرض پوزش هنوز این قابلیت فعال نشده است. 🚧")
            
        elif message.text=="ارزان ترین ها":
            products = Product.objects.filter(category__title=user_sessions[message.chat.id]["current_menu"]).order_by("-price")[:10]
            
        elif message.text=="گران ترین ها":
            products = Product.objects.filter(category__title=user_sessions[message.chat.id]["current_menu"]).order_by("price")[:10]
        
        if products==[]:
            app.send_message(message.chat.id, "متاسفانه این محصول شامل تخفیف نشده است")
            return
        
        elif not products.exists():
            app.send_message(message.chat.id, "🚧 محصولی در این دسته بندی یافت نشد.🚧")
            return
        
        for product in products:
            try:
                send_product_message(app, message, product, current_site)
            except Exception as e:
                app.send_message(message.chat.id, f"the error is: {e}")

##################################


@app.message_handler(state=Support.code)
def handle_product_code(message):
    if subscription_offer(message):
        chat_id = message.chat.id
        product_code = message.text
        if re.match(r'^[A-Z]{4}\d{6}$', message.text):
            
            if Product.objects.get(code=message.text):
                product=Product.objects.get(code=message.text)
                try:
                    send_product_message(app, message, product, current_site)
                except Exception as e:
                    app.send_message(message.chat.id, f"the error is: {e}")
        else:
            app.send_message(chat_id, "🚫 قالب کدی که وارد کرده اید نادرست است. از صحت کد اطمینان حاصل کنید. ⛔️")
        app.delete_state(user_id=message.from_user.id, chat_id=message.chat.id)




#####################################################################################
# support handlers


# Handling the 'Support 👨🏻‍💻' button click event
@app.message_handler(func= lambda message: message.text == "💬 پیام به پشتیبان")
def sup(message):
    app.send_message(chat_id=message.chat.id, text="شروع مکالمه با پشتیبان...\n\nلطفا پیام های خود را ارسال کنید و پس از پایان دکمه پایان مکالمه را فشار دهید:")
    app.set_state(user_id=message.from_user.id, state=Support.text, chat_id=message.chat.id) 


# Handling the user's first message which is saved in 'Support.text' state
@app.message_handler(state=Support.text)
def sup_text(message):
    try:
        sup_markup = types.InlineKeyboardMarkup()
        client_markup = types.InlineKeyboardMarkup()
        
        sup_markup.add(types.InlineKeyboardButton(text="پاسخ", callback_data="پاسخ"))
        client_markup.add(types.InlineKeyboardButton(text="پایان مکالمه", callback_data="پایان مکالمه"))       

        app.send_message(chat_id=5629898030, text=f"Recived a message from <code>{message.from_user.id}</code> with username @{message.from_user.username}:\n\nMessage text:\n<b>{escape_special_characters(message.text)}</b>", reply_markup=sup_markup, parse_mode="HTML")

        app.send_message(chat_id=message.chat.id, text="پیام شما ارسال شد!\n\n لطفا منتظر پاسخ پشتیبان بمانید 🙏🙏🙏", reply_markup=client_markup)

        texts[message.from_user.id] = message.text

        
    except Exception as e:
        app.send_message(chat_id=message.chat.id, text=f"the error is: {e}")




# هندلر برای دکمه "ثبت نام می‌کنم"
@app.message_handler(func=lambda message: message.text == "🔐     ایجاد حساب کاربری    🛡️")
def ask_username(message):
    if subscription_offer(message):
        try:
            app.send_message(message.chat.id, "ممکنه لطفا ایمیلت رو وارد کنی:")
            app.register_next_step_handler(message, pick_email)
        except Exception as e:
            app.send_message(chat_id=message.chat.id, text=f"the error is: {e}")



# hadling any unralted message
@app.message_handler(func=lambda message: app.get_state(user_id=message.from_user.id, chat_id=message.chat.id) is None)
def handle_message(message):
    if subscription_offer(message):
        app.send_message(message.chat.id, "دستور نامعتبر است. لطفاً یکی از گزینه‌های منو را انتخاب کنید.")


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
            app.send_message(chat_id=message.chat.id, text="پیام شما ارسال شد!")

            del texts[user]
            app.delete_state(user_id=message.from_user.id, chat_id=message.chat.id)
        
        except:
            app.send_message(chat_id=user, text=f"Support answer:\n<b>{escape_special_characters(message.text)}</b>", parse_mode="HTML")
            app.send_message(chat_id=message.chat.id, text="پاسخ شما ارسال شد!")

            app.delete_state(user_id=message.from_user.id, chat_id=message.chat.id)
        
    except Exception as e:
        app.send_message(chat_id=message.chat.id, text=f"Something goes wrong...\n\nException:\n<code>{e}</code>", parse_mode="HTML")

    markup = send_menu(message, main_menu, "main_menu", extra_buttons)
    app.send_message(message.chat.id, "لطفا یکی از گزینه های زیر را انتخاب کنید:", reply_markup=markup)




@app.callback_query_handler(func= lambda call: call.data == "پایان مکالمه")
def terminate_chat(call):
    if subscription_offer(call.message):
        try:
            app.delete_state(user_id=call.from_user.id, chat_id=call.message.chat.id)
            app.send_message(chat_id=call.message.chat.id, text=f"مکالمه شما پایان یافت.")
        except Exception as e:
            app.send_message(chat_id=call.message.chat.id, text=f"the error is: {e}")
##################################

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


@app.callback_query_handler(func=lambda call: call.data == 'check_website_subscription')
def check_website_subscription(call):
    if subscription_offer(call.message):
        if not ProfileModel.objects.filter(telegram=call.from_user.username).exists():
            # signup process
            
            app.send_message(call.message.chat.id, "برای خرید و ارسال کالا باید اطلاعات بیشتری (مثل آدرس) از شما داشته باشیم.\n\nابتدا باید حساب کاربری خود را بسازید:")
            home_menue = ["🏡"]
            
            send_menu(call.message, extra_buttons, "create_account", home_menue)
        else:
            # Buy Process
            pass
            


# email validation
def is_valid_email(email):
    print(re.match(r'^[a-z]+$', 'test'))
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'  
    if re.match(email_pattern, email):  
        return True, 'حالا یه نام کاربری برای خودت انتخاب کن:'
    else:  
        return False, "یه جایی این آدرس ایمیلی که نوشتی ایراد داره به نظرم! بگرد پیداش کن درستش کن دوباره برام بنویسش:"
        
        


# گرفتن آدرس ایمیل
def pick_email(message):
    try:
        email = message.text
        
        is_valid, validation_message = is_valid_email(email)  # Assign directly to validation_message
        
        if email in [item['email'] for item in User.objects.values("email")]:
            app.send_message(message.chat.id, "قبل تر از شما کسی با این ایمیل حساب کاربری افتتاح کرده است! می خوای با یه ایمیل دیگه ات امتحان کن:")
            app.register_next_step_handler(message, pick_email)  # Prompt again for email
        else:
            if is_valid:
                username = message.from_user.username
                if username in [item['username'] for item in User.objects.values("username")] + [item['telegram'] for item in ProfileModel.objects.values("telegram")]:
                    app.send_message(message.chat.id, validation_message)  # This now uses validation_message correctly
                    app.register_next_step_handler(message, pick_username, email)  # Proceed to username prompt
                else:
                    app.send_message(message.chat.id, "نام کاربری شما همان ID تلگرام شماست!\n\n حالا یه رمز عبور هشت رقمی شامل حروف برزگ و کوچک عدد و یک علامت‌ برای خودت انتخاب کن:")
                    app.register_next_step_handler(message, pick_password, email, username)
            else:
                app.send_message(message.chat.id, validation_message)  # Re-prompt for a valid email
                app.register_next_step_handler(message, pick_email)  # Prompt again for email
    except Exception as e:
        app.send_message(chat_id=message.chat.id, text=f"the error is: {e}")



# دریافت نام کاربری
def pick_username(message, email):
    try:
        username = message.text
        is_valid, validation_message = validate_username(username)  # Validation message is now separate from `message`
        
        # Send validation message
        app.send_message(message.chat.id, validation_message)
        
        if is_valid:
            # Check if username already exists
            if username in [item['username'] for item in User.objects.values("username")]:
                app.send_message(message.chat.id, "متاسفانه نام کاربری که انتخاب کردی از قبل انتخاب شده لطفا یکی دیگه رو امتحان کن:")
                app.register_next_step_handler(message, pick_username, email)
            else:
                app.send_message(message.chat.id, "عالیه! حالا یه رمز عبور هشت رقمی شامل حروف برزگ و کوچک عدد و یکی از علامت‌ها برای خودت انتخاب کن:")
                app.register_next_step_handler(message, pick_password, email, username)
        else:
            # If the username is invalid, re-prompt the user
            app.register_next_step_handler(message, pick_username, email)
    
    except Exception as e:
        app.send_message(chat_id=message.chat.id, text=f"the error is: {e}")
        
        
# تعیین رمز عبور
def pick_password(message, email, username):
    try:
        password = message.text
        is_valid, validation_message = validate_password(password)
        
        # Send validation message
        app.send_message(message.chat.id, validation_message)
        
        # If password is valid, proceed with registration
        if is_valid:
            
            app.send_message(message.chat.id, "دمت گرم! حالا یه بار دیگه رمزت رو برام بزن تا تاییدش کنم و این بشه رمز عبورت:")
            app.register_next_step_handler(message, pick_password2, email, username, password)
            
        
        # If password is not valid, ask for a new one
        else:
            app.register_next_step_handler(message, pick_password, email, username)
        
    except Exception as e:
        app.send_message(chat_id=message.chat.id, text=f"the error is: {e}")
        
        

# تایید رمز
def pick_password2(message, email, username, password, current_site=current_site):
    if subscription_offer(message):
        try:
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
                
                ProfileModel.objects.create(user=user, fname=message.from_user.first_name, lname=message.from_user.last_name, telegram=message.from_user.username)

                # Trigger activation email
                current_site = current_site # Replace with your actual site domain
                mail_subject = 'Activation link has been sent to your email id'
                telegram_activation_link = f"https://t.me/hussein2079_bot?start=activate_{urlsafe_base64_encode(force_bytes(user.pk))}_{generate_token.make_token(user)}"

                message_content = render_to_string('registration/acc_active_email.html', {
                    'user': user,
                    'domain': current_site[8:],
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': generate_token.make_token(user),
                    'telegram': True,
                    'telegram_activation_link': telegram_activation_link
                })
                
                email = EmailMessage(
                    mail_subject, message_content, to=[email]
                )
                email.content_subtype = "html"
                email.send()
                
                # app.send_message(message.chat.id, f"{message.from_user.first_name} عزیز افتتاح حساب شما تکمیل شد. شما اکنون کاربر طلایی هستید. به علاوه از همین حالا می تونید از پنج روز عضویت ویژه استفاده کنید.")
                
                app.send_message(message.chat.id, "دوست عزیزم یک ایمیل از طرف شرکت اینتلیوم برای شما ارسال شده است که حاوی لینک فعالسازی حساب شماست لطفا روی آن کلیک کنید.")
                # app.register_next_step_handler(message, )
            else:
                app.send_message(message.chat.id, "تایید رمز عبور با رمز عبوری که از قبل وارد کردید تطابق ندارد. لطفا دباره آن را دقیقا مثل قبل وارد کنید:")
                app.register_next_step_handler(message, pick_password2, email, username, password)
        except Exception as e:
            app.send_message(chat_id=message.chat.id, text=f"the error is: {e}")

app.add_custom_filter(custom_filters.StateFilter(app))