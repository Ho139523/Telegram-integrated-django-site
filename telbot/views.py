#General imports
from telebot import TeleBot, types


# Variables imports
from utils.variables.TOKEN import TOKEN

# start handler imports
import requests
import random


# start: KeyboardButtton for forced subscription
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from utils.variables.CHANNELS import my_channels_with_atsign, my_channels_without_atsign


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
import json
import telebot.types
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import logging

logger = logging.getLogger(__name__)
from django.views.decorators.csrf import csrf_exempt
import subprocess
from utils.telbot.functions import *
localtunnel_password = get_tunnel_password()
current_site = get_current_site()
current_webhook = get_current_webhook()





# Webhook settings
logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class TelegramBotWebhookView(View):
    def post(self, request, *args, **kwargs):
        try:
            json_str = request.body.decode('UTF-8')
            logger.info(f"Received data: {json_str}")  # لاگ درخواست دریافتی
            update = telebot.types.Update.de_json(json.loads(json_str))
            app.process_new_updates([update])  # پردازش پیام توسط ربات
            return JsonResponse({"status": "success"}, status=200)
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=200)  # همیشه HTTP 200 برگردانید
            
            

# Check subscription
def check_subscription(user, channels=my_channels_with_atsign):
    for channel in channels:
        is_member = app.get_chat_member(chat_id=channel, user_id=user)
        
        if is_member.status in ["kicked", "left"]:
            
            return False
        
        return True





# Generate random product data
def generate_product_data(category):
    products = []
    for _ in range(20):
        product = {
            'title': f"{category} Product {random.randint(1000, 9999)}",
            'description': f"Description for {category} product {random.randint(1000, 9999)}",
            'stock': random.choice([True, False]),
            'pic1': "https://www.example.com/sample-product.jpg",  # Replace with actual image URL
            'pic2': "https://www.example.com/sample-product2.jpg",
            'pic3': "https://www.example.com/sample-product3.jpg",
            'pic4': "https://www.example.com/sample-product4.jpg",
            'off': random.randint(5, 50),
            'code': str(random.randint(100000000, 999999999)),
            'price': random.randint(1000000, 50000000),
            'final_price': lambda price, off: price * (1 - off / 100)
        }
        products.append(product)
    return products




# start handler
@app.message_handler(commands=['start'])
def start(message):
    
    # User Info
    tel_id = message.from_user.username if message.from_user.username else message.from_user.id
    tel_name = message.from_user.first_name
    

    # Make a POST request to the registration API
    response = requests.post(f"{current_site}/api/check-registration/", json={"tel_id": tel_id})
    
    
    # Create keyboard for subscription check
    channel_markup = types.InlineKeyboardMarkup()
    check_subscription_button = types.InlineKeyboardButton(text='عضو شدم.', callback_data='check_subscription')
    channel_subscription_button = types.InlineKeyboardButton(text='در کانال ما عضو شوید...', url=f"https://t.me/{my_channels_without_atsign[0]}")
    group_subscription_button = types.InlineKeyboardButton(text="در گروه ما عضو شوید...", url=f"https://t.me/{my_channels_without_atsign[1]}")
    
    channel_markup.add(channel_subscription_button, group_subscription_button)
    channel_markup.add(check_subscription_button)

    # Handle the response based on status code
    if response.status_code == 201:
        app.send_message(message.chat.id, f"🏆 {tel_name} عزیز ثبت نامت با موفقیت انجام شد.\n\n")
    else:
        app.send_message(message.chat.id, f"{tel_name} عزیز شما قبلا در ربات ثبت نام کرده‌اید.")
        
    
    is_member = check_subscription(user=message.from_user.id)
    
    if is_member==False:
        app.send_message(message.chat.id, "برای تایید عضویت خود در گروه و کانال بر روی دکمه‌ها کلیک کنید.", reply_markup=channel_markup)
    
    else:
        # Display the main menu
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("موجودی من", "خرید با کد کالا", "دسته بندی ها", "منو اصلی")
        app.send_message(call.message.chat.id, "انتخاب کنید:", reply_markup=markup)


        
        
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
        

# Balance handler
@app.message_handler(func=lambda message: message.text == "موجودی من")
def show_balance(message):
    user_id = message.from_user.id
    balance = users.get(user_id, {}).get('balance', 0)
    app.send_message(message.chat.id, f"موجودی شما: {balance} تومان")    
        
        
# Category handler
@app.message_handler(func=lambda message: message.text == "دسته بندی ها")
def show_categories(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("پوشاک", "خوراکی", "دیجیتال", "بازگشت به منو قبلی")
    app.send_message(message.chat.id, "لطفاً دسته بندی مورد نظر را انتخاب کنید:", reply_markup=markup)


# Handle category selection
@app.message_handler(func=lambda message: message.text in ["پوشاک", "خوراکی", "دیجیتال"])
def handle_category(message):
    category = message.text
    products = generate_product_data(category)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if category == "پوشاک":
        markup.add("ورزشی", "کت و شلوار", "زمستانه", "کفش و کتونی", "تابستانه", "بازگشت به منو قبلی")
    elif category == "خوراکی":
        markup.add("خشکبار", "خوار و بار", "سوپر مارکت", "بازگشت به منو قبلی")
    elif category == "دیجیتال":
        markup.add("لپتاب", "گوشی", "بازگشت به منو قبلی")
    
    app.send_message(message.chat.id, f"لطفاً زیر دسته بندی {category} را انتخاب کنید:", reply_markup=markup)



# Handle subcategory selection
@app.message_handler(func=lambda message: message.text in ["ورزشی", "کت و شلوار", "زمستانه", "کفش و کتونی", "تابستانه", "خشکبار", "خوار و بار", "سوپر مارکت", "لپتاب", "گوشی"])
def handle_subcategory(message):
    subcategory = message.text
    products = generate_product_data(subcategory)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("پر فروش ترین ها", "گران ترین ها", "ارزان ترین ها", "پر تخفیف ها", "بازگشت به منو قبلی")
    app.send_message(message.chat.id, f"لطفاً یکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=markup)



# Show products based on selected option (best-selling, most expensive, etc.)
@app.message_handler(func=lambda message: message.text in ["پر فروش ترین ها", "گران ترین ها", "ارزان ترین ها", "پر تخفیف ها"])
def show_products(message):
    option = message.text
    products = generate_product_data("Random Category")  # Replace with actual category products
    selected_products = random.sample(products, 10)  # Select 10 random products for display
    
    for product in selected_products:
        title = product['title']
        description = product['description']
        price = product['price']
        off = product['off']
        final_price = product['final_price'](price, off)
        stock = "موجود" if product['stock'] else "ناموجود"
        pic1 = product['pic1']
        pic2 = product['pic2']
        pic3 = product['pic3']
        pic4 = product['pic4']
        
        message_text = f"{title}\n{description}\n قیمت فقط: {price}\n تخفیف: {off}%\n قیمت نهایی: {final_price} تومان\n {stock}"
        markup = types.InlineKeyboardMarkup()
        buy_button = types.InlineKeyboardButton(text="خرید", callback_data=f"buy_{product['code']}")
        markup.add(buy_button)
        
        app.send_message(message.chat.id, message_text, reply_markup=markup)



# Handle buy action (checking balance)
@app.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def handle_buy(call):
    product_code = call.data.split('_')[1]
    user_id = call.from_user.id
    product = get_product_by_code(product_code)
    
    if product:
        balance = users.get(user_id, {}).get('balance', 0)
        price = product['final_price'](product['price'], product['off'])
        
        if balance >= price:
            users[user_id]['balance'] -= price
            app.send_message(call.message.chat.id, "خرید موفقیت آمیز بود!")
        else:
            app.send_message(call.message.chat.id, "موجودی شما کافی نیست!")
    else:
        app.send_message(call.message.chat.id, "کالا یافت نشد!")



# Implement back navigation for all menus
@app.message_handler(func=lambda message: message.text == "بازگشت به منو قبلی")
def back_to_previous_menu(message):
    show_categories(message)

