from utils.variables.TOKEN import TOKEN
import requests
import subprocess
import re
from telebot import TeleBot
from telebot.types import Message
from telebot.storage import StateMemoryStorage
from accounts.models import ProfileModel
from products.models import Product, Category, ProductImage, ProductAttribute, Store
import os
from django.conf import settings
import requests
from django.core.files.base import ContentFile


# send_product_message function
from telebot import types


# bot settings
from telebot.storage import StateMemoryStorage
state_storage = StateMemoryStorage()
app = TeleBot(token=TOKEN, state_storage=state_storage)


from telbot.sessions import session_manager

# Access shared user_sessions
user_sessions = session_manager.user_sessions

from utils.telbot.variables import *
from pathlib import Path
import os
import requests
from django.conf import settings

from utils.telbot.variables import home_menu
import traceback

def get_tunnel_password():
    try:
        result = subprocess.run(
            ["curl", "-s", "https://loca.lt/mytunnelpassword"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            password = result.stdout.strip()  # حذف فاصله‌ها و خط‌های اضافی
            return password
        else:
            print("Error fetching password:", result.stderr)
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
        
        

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
    
    
    
def send_product_message(app, product, current_site, message=None, buttons=True, channel_id=None):
    try:
        if message:
            chat_id = message.chat.id
            message_data = {
                "chat_id": chat_id,
                "username": message.from_user.username,
                "first_name": message.from_user.first_name
            }
        else:
            chat_id = channel_id
        formatted_price = "{:,.0f}".format(float(product.price))
        formatted_final_price = "{:,.0f}".format(float(product.final_price))
        
        if product.discount > 0:
            price_text = (
                f"🏃 {product.discount} % تخفیف\n"
                f"💵 قیمت: <s>{formatted_price}</s> تومان ⬅ {formatted_final_price} تومان"
            )
        else:
            price_text = f"💵 قیمت: {formatted_price} تومان"
            
        # for att in product.
        
        attributes = product.attributes.filter(product=product)

        # تولید متن ویژگی‌ها
        if attributes.exists():
            attribute_text = "\n✅ ".join([f"{attr.key}: {attr.value}" if attr.value else f"{attr.key}" for attr in attributes])
            attribute_text = f"✅ {attribute_text}\n\n"  # اضافه کردن تیک سبز فقط در صورت وجود ویژگی‌ها
        else:
            attribute_text = ""  # در صورت نبود ویژگی، متن ویژگی‌ها خالی باشد
        
        brand_text = f"🔖 برند کالا: {product.brand}\n" if product.brand else ""
        description_text = f"{product.description}\n" if product.description else ""
        caption = (
            f"\n⭕️ نام کالا: {product.name}\n"
            f"{brand_text}"
            f"کد کالا: {product.code}\n\n"
            f"{description_text}\n"
            f"{attribute_text}"
            f"🔘 فروش با ضمانت ارویجینال💯\n"
            f"📫 ارسال به تمام نقاط کشور\n\n"
            f"{price_text}\n"
        )

        # Prepare photos
        photos = [
            types.InputMediaPhoto(open(product.main_image.path, 'rb'), caption=caption, parse_mode='HTML')
        ] + [
            types.InputMediaPhoto(open(i.image.path, 'rb')) for i in product.image_set.all()
        ]
        
        if len(photos) > 10:
            photos = photos[:10]  # Limit to 10 photos
        
        # Send product photos and message
        app.send_media_group(chat_id, media=photos)
        
        # Create inline keyboard markup
        if buttons:
            url = current_site + "/buy/"

            # درخواست برای دریافت اطلاعات محصول
            product_response = requests.get(current_site + "/api/products/", params={"code": product.code})

            # بررسی وضعیت پاسخ
            # print("Product Response Status Code:", product_response.status_code)
            # print("Product Response Content:", product_response.text)

            if product_response.status_code == 200:
                try:
                    # داده‌های محصول را از پاسخ دریافت کنید
                    product_data = product_response.json()
                    # print("Product Data:", product_data)
                    
                    # ارسال اطلاعات محصول به تابع خرید
                    
                    response = requests.post(url, json={"data": product_data, "message": message_data})
                    # print("Buy Response Status Code:", response.status_code)
                    # print("Buy Response Content:", response.text)

                    if response.status_code == 200:
                        # دریافت URL بازگشتی برای خرید
                        redirect_url = response.json().get("redirect_url")
                        markup = types.InlineKeyboardMarkup()
                        buy_button = types.InlineKeyboardButton(text="💰 خرید", url=redirect_url)
                        markup.add(buy_button)
                        app.send_message(
                            chat_id,
                            "برای خرید یا افزودن کالا به سبد خرید کلیک کنید 👇👇👇",
                            reply_markup=markup
                        )
                    else:
                        app.send_message(chat_id, "مشکلی در پردازش درخواست خرید به وجود آمد.")
                except Exception as e:
                    print("Error while processing product data:", e)
                    app.send_message(chat_id, "خطایی در پردازش اطلاعات محصول رخ داد.")
            else:
                app.send_message(chat_id, "مشکلی در دریافت اطلاعات کالا به وجود آمد.")

    except Exception as e:
        print(f"your error is: {e}")


############################  CHECK SUBSCRIPTION  ############################

import logging
from utils.variables.CHANNELS import my_channels_with_atsign, my_channels_without_atsign

logger = logging.getLogger(__name__)

class SubscriptionClass:
    def __init__(self, bot: TeleBot):
        self.bot = bot
        self.my_channels_with_atsign = my_channels_with_atsign
        self.my_channels_without_atsign = my_channels_without_atsign
        self.current_site = 'https://intelleum.ir'
        
    def handle_check_subscription(self, call: types.CallbackQuery):
        """✅ بررسی عضویت هنگام کلیک روی دکمه 'عضو شدم'"""
        chat_id = call.message.chat.id
        user_id = call.from_user.id

        

        # بررسی عضویت
        is_member = self.check_subscription(user_id)  

        if is_member:
            
            try:
            
                # ✅ پاسخ اولیه به Callback Query
                self.bot.answer_callback_query(call.id, "🔄 در حال بررسی عضویت شما...", show_alert=False)
                self.bot.edit_message_text("🎉 عضویت شما تایید شد. حالا می‌توانید از امکانات ربات استفاده کنید.",
                                      chat_id=chat_id, message_id=call.message.message_id)

                profile = ProfileModel.objects.get(tel_id=user_id)
                main_menu = profile.tel_menu
                extra_buttons = profile.extra_button_menu
                markup = send_menu(call.message, main_menu, "main_menu", extra_buttons)

                self.bot.send_message(user_id, "لطفاً یکی از گزینه‌ها را انتخاب کنید:", reply_markup=markup)
            except Exception as e:
                self.bot.send_message(user_id, f"error iis: {e}")
        else:
            self.bot.answer_callback_query(call.id, "❌ شما هنوز در کانال عضو نشده‌اید.", show_alert=True)

    def register_handlers(self):
        """🔹 ثبت هندلرهای مورد نیاز"""
        self.bot.callback_query_handler(func=lambda call: call.data == "check_subscription2")(self.handle_check_subscription)

    def check_subscription(self, user, channels=None):
        """✅ بررسی می‌کند که کاربر در کانال عضو شده است یا نه"""
        if channels is None:
            channels = self.my_channels_with_atsign
        for channel in channels:
            try:
                is_member = self.bot.get_chat_member(chat_id=channel, user_id=user)
                if is_member.status in ["kicked", "left"]:
                    return False
            except Exception as e:
                logger.error(f"🚨 خطا در بررسی عضویت کاربر {user} در کانال {channel}: {e}")
                return False
        return True
        
    def subscription_offer(self, message):
        """❌ اگر کاربر عضو نباشد، دکمه‌های عضویت نمایش داده شوند"""
        channel_markup = types.InlineKeyboardMarkup()
        check_subscription_button = types.InlineKeyboardButton(text='✅ عضو شدم', callback_data='check_subscription2')
        channel_subscription_button = types.InlineKeyboardButton(text='📢 در کانال ما عضو شوید', url=f"https://t.me/{self.my_channels_without_atsign[0]}")
        group_subscription_button = types.InlineKeyboardButton(text="💬 در گروه ما عضو شوید", url=f"https://t.me/{self.my_channels_without_atsign[1]}")

        channel_markup.add(channel_subscription_button, group_subscription_button)
        channel_markup.add(check_subscription_button)

        if not self.check_subscription(user=message.from_user.id):
            self.bot.send_message(message.chat.id, "❌ برای تایید عضویت خود در گروه و کانال بر روی دکمه‌ها کلیک کنید.", reply_markup=channel_markup)
            return False
        return True
       
############################  SEND MENU  ############################
subscription = SubscriptionClass(app)

# Helper function to send menu
def send_menu(message, options, current_menu, extra_buttons=None):
    """Send a menu with options and update the session."""
    if subscription.subscription_offer(message):
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

############################  SEE PRODUCTS  ############################

# Top discounts
def handle_products(message):
    from utils.telbot.variables import retun_menue
    if subscription.subscription_offer(message):
        chat_id = message.chat.id
        subcategory = message.text  # Save subcategory
        options = ["پر فروش ترین ها", "گران ترین ها", "ارزان ترین ها", "پر تخفیف ها"]

        # Save session
        # home_menue = ["🏡"]
        markup = send_menu(message, options, "products", retun_menue)
        session = user_sessions[message.chat.id]
        current_category = Category.objects.get(title__iexact=session["current_menu"], status=True)
        app.send_message(message.chat.id, f"{current_category.get_full_path()}", reply_markup=markup)

############################  CATEGORY MENU  ############################

class CategoryClass:
    
    def __init__(self):
        pass
        
    # First Layer category
    def handle_category(self, message):
        if subscription.subscription_offer(message):
            try:
                cats = Category.objects.filter(parent__isnull=True, status=True).values_list('title', flat=True)
                home_menue = ["🏡"]
                markup = send_menu(message, cats, message.text, home_menue)
                app.send_message(message.chat.id, "کالایی که دنبالشی جزو کدام دسته است", reply_markup=markup)
            except Exception as e:
                app.send_message(message.chat.id, "خطایی رخ داده است. لطفاً دوباره تلاش کنید.")
                print(f"Error: {e}")

            
            

    # second layer category
    def handle_subcategory(self, message):
        from utils.telbot.variables import retun_menue
        try:
            if subscription.subscription_offer(message):
                current_category = Category.objects.get(title__iexact=message.text.title(), status=True)
                
                # Get the titles of the child categories
                children = [child.title for child in current_category.get_next_layer_categories()]
                
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
                    app.send_message(message.chat.id, f"{Category.objects.get(title__iexact=session["current_menu"], status=True).get_full_path()}", reply_markup=markup)
                
        except Exception as e:
            app.send_message(message.chat.id, "خطایی رخ داده است. لطفاً دوباره تلاش کنید.")
            print(f"Error: {e}")


############################  ADD PRODUCT  ############################

# ایجاد slug یکتا
def generate_unique_slug(model, name):
    from django.utils.text import slugify
    
    slug = slugify(name)
    unique_slug = slug
    counter = 1
    while model.objects.filter(slug=unique_slug).exists():
        unique_slug = f"{slug}-{counter}"
        counter += 1
    return unique_slug



def download_and_save_image(file_id, bot):
    try:
        # دانلود فایل
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        # مسیر ذخیره‌سازی
        save_dir = os.path.join(settings.MEDIA_ROOT, "product_images")
        os.makedirs(save_dir, exist_ok=True)  # ایجاد مسیر در صورت عدم وجود
        
        file_path = os.path.join(save_dir, file_info.file_path.split('/')[-1])

        # ذخیره فایل در سیستم
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        return file_path  # مسیر ذخیره‌شده را برمی‌گرداند
    except Exception as e:
        print(f"خطا در ذخیره تصویر: {e}")
        return None






class ProductBot:
    def __init__(self, bot: TeleBot):
        self.bot = bot
        self.user_data = {}
        self.product_state = self.ProductState()

    class ProductState:
        NAME = "name"
        SLUG = "slug"
        BRAND = "brand"
        PRICE = "price"
        DISCOUNT = "discount"
        STOCK = "stock"
        STATUS = "status"
        CATEGORY = "category"
        DESCRIPTION = "description"
        CODE = "code"
        MAIN_IMAGE = "main_image"
        ADDITIONAL_IMAGES = "additional_images"
        ATTRIBUTES = "attributes"
        DELETE = "delete"
        
        def __init__(self):
            self.user_menus = {}
        
        def update_user_menu(self, chat_id, menu_title):
            self.user_menus[chat_id] = menu_title
            
        def get_user_menu(self, chat_id):
            return self.user_menus.get(chat_id, None)



    def register_handlers(self):
        """Register message handlers."""
        self.bot.register_message_handler(self.cancle_request, func=lambda message: message.text == "منصرف شدم")
        self.bot.register_message_handler(self.get_name, func=self.is_state(self.ProductState.NAME))
        self.bot.register_message_handler(self.get_brand, func=self.is_state(self.ProductState.BRAND))
        self.bot.register_message_handler(self.get_price, func=self.is_state(self.ProductState.PRICE))
        self.bot.register_message_handler(self.get_discount, func=self.is_state(self.ProductState.DISCOUNT))
        self.bot.register_message_handler(self.get_stock, func=self.is_state(self.ProductState.STOCK))
        self.bot.register_message_handler(self.get_status, func=self.is_state(self.ProductState.STATUS))
        self.bot.register_message_handler(self.get_category, func=self.is_state(self.ProductState.CATEGORY))
        self.bot.register_message_handler(self.get_description, func=self.is_state(self.ProductState.DESCRIPTION))
        self.bot.register_message_handler(self.get_product_attributes, func=self.is_state(self.ProductState.ATTRIBUTES))
        self.bot.register_message_handler(self.get_main_image, func=self.is_state(self.ProductState.MAIN_IMAGE), content_types=["photo"])
        self.bot.register_message_handler(self.get_additional_images, func=self.is_state(self.ProductState.ADDITIONAL_IMAGES), content_types=["photo"])
        self.bot.register_message_handler(self.delete, func=self.is_state(self.ProductState.DELETE))

    def is_state(self, state):
        """Check if the current state matches the given state."""
        def check(message: Message):
            return self.user_data.get(message.chat.id, {}).get("state") == state
        return check

    def set_state(self, chat_id, state):
        """Set the state for a user."""
        if chat_id not in self.user_data:
            self.user_data[chat_id] = {}
        self.user_data[chat_id]["state"] = state

    def save_user_data(self, chat_id, key, value):
        """Save user data for the current session."""
        if chat_id not in self.user_data:
            self.user_data[chat_id] = {}
        self.user_data[chat_id][key] = value

    def reset_state(self, chat_id):
        """Reset user state."""
        if chat_id in self.user_data:
            self.user_data.pop(chat_id)

    # def start(self, message: Message):
        # """Start the product addition process."""
        # self.set_state(message.chat.id, self.ProductState.NAME)
        # self.bot.send_message(message.chat.id, "لطفاً نام محصول را وارد کنید:")

    def get_name(self, message: Message):
        self.save_user_data(message.chat.id, "name", message.text)
        self.set_state(message.chat.id, self.ProductState.BRAND)
        markup = send_menu(message, ["بدون برند"], message.text, ["منصرف شدم"])
        self.bot.send_message(message.chat.id, "لطفاً برند محصول را وارد کنید (اختیاری):", reply_markup=markup)

    def get_brand(self, message: Message):
        if message.text == "بدون برند":
            self.save_user_data(message.chat.id, "brand", None)
        else:
            self.save_user_data(message.chat.id, "brand", message.text)
        self.set_state(message.chat.id, self.ProductState.PRICE)
        markup = send_menu(message, ["منصرف شدم"], message.text)
        self.bot.send_message(message.chat.id, "لطفاً قیمت محصول را وارد کنید:", reply_markup=markup)

    def get_price(self, message: Message):
        try:
            # تلاش برای تبدیل پیام به عدد
            price = float(message.text)

            # بررسی اینکه قیمت معتبر است یا خیر
            if price < 10000:
                self.bot.send_message(
                    message.chat.id,
                    "❌ قیمت وارد شده کمتر از حد مجاز (10000) است. لطفاً قیمتی معتبر وارد کنید:"
                )
                return  # خروج از تابع تا کاربر دوباره قیمت وارد کند

            # ذخیره قیمت در داده‌های کاربر
            self.save_user_data(message.chat.id, "price", price)
            self.set_state(message.chat.id, self.ProductState.DISCOUNT)

            # ارسال پیام برای درخواست درصد تخفیف
            self.bot.send_message(message.chat.id, "درصد تخفیف را وارد کنید:")
        except ValueError:
            # مدیریت خطای تبدیل مقدار نامعتبر
            self.bot.send_message(
                message.chat.id,
                "❌ قیمت باید یک عدد باشد! لطفاً دوباره تلاش کنید:"
            )

    def get_discount(self, message: Message):
        try:
            # تلاش برای تبدیل تخفیف به عدد
            discount = float(message.text)

            # دریافت قیمت و محاسبه قیمت نهایی
            user_data = self.user_data.get(message.chat.id, {})
            price = user_data.get("price", 0)
            final_price = price - ((price * discount) / 100)

            # بررسی اینکه قیمت نهایی معتبر است یا خیر
            if final_price < 10000:
                self.bot.send_message(
                    message.chat.id,
                    "❌ قیمت نهایی پس از تخفیف کمتر از حد مجاز (10000) است. لطفاً دوباره قیمت اصلی را وارد کنید:"
                )
                self.set_state(message.chat.id, self.ProductState.PRICE)  # بازگشت به مرحله قیمت
                return

            # ذخیره تخفیف در داده‌های کاربر و ادامه به مرحله بعد
            self.save_user_data(message.chat.id, "discount", discount)
            self.set_state(message.chat.id, self.ProductState.STOCK)

            # ارسال پیام برای دریافت توضیحات
            self.bot.send_message(message.chat.id, "موجودی محصول را وارد کنید:")
        except ValueError:
            # مدیریت خطای تبدیل مقدار نامعتبر
            self.bot.send_message(
                message.chat.id,
                "❌ درصد تخفیف باید یک عدد باشد! لطفاً دوباره تلاش کنید:"
            )


    def get_stock(self, message: Message):
        try:
            stock = int(message.text)
            self.save_user_data(message.chat.id, "stock", stock)
            markup = send_menu(message, ["فعال", "غیر فعال"], message.text, ["منصرف شدم"])
            app.send_message(message.chat.id, "آیا وضعیت کالا فعال است؟:", reply_markup=markup)
            self.set_state(message.chat.id, self.ProductState.STATUS)
        except ValueError:
            self.bot.send_message(message.chat.id, "موجودی باید یک عدد صحیح باشد!")

    def get_status(self, message: Message):
        try:
            status = message.text.strip()
            
            # ذخیره وضعیت موجود بودن کالا
            if status=="فعال":
                self.save_user_data(message.chat.id, "status", True)
            else:
                self.save_user_data(message.chat.id, "status", False)
            
            # نمایش منوی دسته‌بندی اصلی
            self.display_category_menu(message, None)
        except Exception as e:
            self.bot.send_message(message.chat.id, "خطایی رخ داده است. لطفاً دوباره تلاش کنید.")
            print(f"Error: {e}")


    def display_category_menu(self, message, parent_category_title=None):
        try:
            # مدیریت دکمه بازگشت
            if message.text == "🔙":
                previous_menu = self.product_state.get_user_menu(message.chat.id)
                
                if previous_menu:
                    try:
                        parent_category = Category.objects.get(title__iexact=previous_menu, status=True)
                        
                        if parent_category.parent:
                            # بازگشت به دسته‌بندی والد
                            self.product_state.update_user_menu(message.chat.id, parent_category.parent.title)
                            category_titles = Category.objects.filter(parent=parent_category.parent, status=True).values_list("title", flat=True)
                            markup = send_menu(message, category_titles, parent_category_title or "انتخاب دسته‌بندی", retun_menue)
                            self.bot.send_message(
                                message.chat.id,
                                "لطفاً دسته‌بندی مناسب برای کالای خود را انتخاب کنید:",
                                reply_markup=markup
                            )
                        else:
                            # بازگشت به منوهای سطح اول
                            self.product_state.update_user_menu(message.chat.id, None)
                            categories = Category.objects.filter(parent__isnull=True, status=True)
                            category_titles = [category.title for category in categories]
                            markup = send_menu(message, category_titles, "انتخاب دسته‌بندی اصلی", home_menu)
                            self.bot.send_message(
                                message.chat.id,
                                "لطفاً دسته‌بندی اصلی را انتخاب کنید:",
                                reply_markup=markup
                            )
                    except Category.DoesNotExist:
                        # اگر دسته‌بندی قبلی معتبر نبود
                        self.bot.send_message(
                            message.chat.id, 
                            "دسته‌بندی قبلی معتبر نیست. لطفاً دوباره انتخاب کنید."
                        )
                return

            # بررسی دسته‌بندی والد
            if not parent_category_title:
                categories = Category.objects.filter(parent__isnull=True, status=True)
                menu_type = home_menu  # اگر دسته‌بندی والد ندارد، از home_menu استفاده کنید
            else:
                parent_category = Category.objects.get(title__iexact=parent_category_title, status=True)
                categories = parent_category.get_next_layer_categories()
                menu_type = retun_menue  # اگر دسته‌بندی والد دارد، از retun_menue استفاده کنید

            # استخراج عنوان دسته‌بندی‌ها
            category_titles = [category.title for category in categories]

            # نمایش دسته‌بندی‌ها
            if category_titles:
                markup = send_menu(message, category_titles, parent_category_title or "انتخاب دسته‌بندی", menu_type)
                self.bot.send_message(
                    message.chat.id,
                    "لطفاً دسته‌بندی مناسب برای کالای خود را انتخاب کنید:",
                    reply_markup=markup
                )
                self.product_state.update_user_menu(message.chat.id, parent_category_title)
                self.set_state(message.chat.id, self.ProductState.CATEGORY)

        except Exception as e:
            self.bot.send_message(message.chat.id, "خطایی رخ داده است. لطفاً دوباره تلاش کنید.")
            print(f"Error: {e}")







    def get_category(self, message: Message):
        try:
            selected_category_title = message.text.strip()
            
            if message.text == "🔙":
                self.display_category_menu(message, selected_category_title)
                return 
            
            # بررسی وجود دسته‌بندی انتخابی
            elif not Category.objects.filter(title__iexact=selected_category_title, status=True).exists():
                self.bot.send_message(message.chat.id, "دسته‌بندی انتخابی معتبر نیست. لطفاً دوباره انتخاب کنید.")
                return

            # ذخیره دسته‌بندی انتخاب شده
            self.save_user_data(message.chat.id, "category", selected_category_title)

            # بررسی زیر دسته‌ها
            selected_category = Category.objects.get(title__iexact=selected_category_title, status=True)
            if selected_category.get_next_layer_categories():
                # نمایش زیر دسته‌ها
                self.display_category_menu(message, selected_category_title)
            else:
                # پایان فرآیند انتخاب دسته‌بندی
                self.bot.send_message(message.chat.id, f"دسته‌بندی انتخاب شده: {selected_category.get_full_path()}")
                self.save_user_data(message.chat.id, "category", selected_category)
                self.set_state(message.chat.id, self.ProductState.DESCRIPTION)
                main_menu = ProfileModel.objects.get(tel_id=message.from_user.id).tel_menu
                markup = send_menu(message, ["توضیحات ندارد"], "main menu", ["منصرف شدم"])
                self.bot.send_message(message.chat.id, "لطفاً توضیحات محصول را وارد کنید (اختیاری):", reply_markup=markup)
        except Exception as e:
            error_details = traceback.format_exc()
            custom_message = f"An error occurred: {e}\nDetails:\n{error_details}"
            self.bot.send_message(message.chat.id, f"{custom_message}")



    def get_description(self, message: Message):
        self.save_user_data(message.chat.id, "product_attributes", {})
        if message.text == "توضیحات ندارد":
            self.save_user_data(message.chat.id, "description", None)
        else:
            self.save_user_data(message.chat.id, "description", message.text)
        self.set_state(message.chat.id, self.ProductState.ATTRIBUTES)
        markup = types.InlineKeyboardMarkup()
        finish_button = types.InlineKeyboardButton(text="هیچ ویژگی تبلیغاتی مد نظرم نیست ...!", callback_data="finish_attributes")
        markup.add(finish_button)
        
        self.bot.send_message(
            message.chat.id, 
            "لطفاً ویژگی‌های تبلیغاتی محصول را یک به یک بنویسید و در انتها دکمه پایان را ارسال کنید.",
            reply_markup=markup
        )
        markup = send_menu(message, [], "main menu", ["منصرف شدم"])
        self.bot.edit_message_reply_markup(
            chat_id=message.chat.id,
            message_id=message.message_id,
            reply_markup=markup
        )


    def get_product_attributes(self, message: Message):
        # نمایش پیام برای وارد کردن ویژگی‌های محصول
        markup = types.InlineKeyboardMarkup()
        finish_button = types.InlineKeyboardButton(text="پایان", callback_data="finish_attributes")
        markup.add(finish_button)
        
        key = message.text.split(":")[0]  # کلید ویژگی (مانند "وزن")
        if ":" not in message.text:
            value = ""
        else:
            value = message.text.split(":")[1]  # مقدار ویژگی (مانند "1kg")
        user_data = self.user_data.get(message.chat.id, {})
        product_attributes = user_data["product_attributes"]
        product_attributes[key] = value
        
        self.save_user_data(message.chat.id, "product_attributes", product_attributes)
        
        self.bot.send_message(
            message.chat.id, 
            "لطفاً ویژگی‌های تبلیغاتی محصول را یک به یک بنویسید و در انتها دکمه پایان را ارسال کنید.",
            reply_markup=markup
        )
        self.set_state(message.chat.id, self.ProductState.ATTRIBUTES)  # وضعیت به حالت ویژگی‌های محصول تغییر می‌کن

    
    def handle_finish_attributes(self, callback_query: types.CallbackQuery):
        try:
            chat_id = callback_query.message.chat.id
            
            self.set_state(chat_id, self.ProductState.MAIN_IMAGE)
            self.bot.send_message(chat_id, "لطفاً تصویر اصلی محصول را ارسال کنید:")
        except Exception as e:
            self.bot.send_message(callback_query.message.chat.id, "خطا در ذخیره ویژگی رخ داده است.")
            print(f"Error: {e}")
        
        
    def register_handle_finish_attributes(self):
        self.bot.callback_query_handler(func=lambda call: call.data == 'finish_attributes')(self.handle_finish_attributes)

    

    def get_main_image(self, message: Message):
        try:
            # دانلود و ذخیره تصویر
            file_id = message.photo[-1].file_id
            saved_path = download_and_save_image(file_id, self.bot)
            if saved_path:
                self.save_user_data(message.chat.id, "main_image", saved_path)  # ذخیره مسیر تصویر
                self.set_state(message.chat.id, self.ProductState.ADDITIONAL_IMAGES)
                self.bot.send_message(message.chat.id, "لطفاً 3 تصویر اضافی برای محصول ارسال کنید:")
            else:
                self.bot.send_message(message.chat.id, "خطا در ذخیره تصویر اصلی رخ داده است.")
        except Exception as e:
            self.bot.send_message(message.chat.id, "خطایی رخ داده است. لطفاً دوباره تلاش کنید.")
            print(f"Error: {e}")



    def get_additional_images(self, message: Message):
        try:
            # بازیابی تصاویر اضافی
            additional_images = self.user_data[message.chat.id].get("additional_images", [])
            file_id = message.photo[-1].file_id

            # دانلود و ذخیره تصویر
            saved_image = download_and_save_image(file_id, self.bot)
            
            if saved_image:
                additional_images.append(saved_image)  # ذخیره مسیر تصویر
                self.save_user_data(message.chat.id, "additional_images", additional_images)
            else:
                self.bot.send_message(message.chat.id, "یکی از تصاویر اضافی ذخیره نشد. لطفاً دوباره تلاش کنید.")

            # بررسی تعداد تصاویر
            if len(additional_images) >= 3:
                # بازیابی اطلاعات کاربر
                user_data = self.user_data.get(message.chat.id, {})
                slug = generate_unique_slug(Product, user_data["name"])
                # ایجاد و ذخیره محصول
                product = Product.objects.create(
                    profile=ProfileModel.objects.get(tel_id=message.from_user.id),
                    name=user_data["name"],
                    slug=slug,
                    brand=user_data["brand"],
                    price=user_data["price"],
                    discount=user_data["discount"],
                    stock=user_data["stock"],
                    status=user_data["status"],
                    category=user_data["category"],
                    description=user_data["description"],
                    main_image=user_data["main_image"],
                )
                
                for key, value in user_data["product_attributes"].items():
                    ProductAttribute.objects.create(
                        product=product,
                        key=key,  # کلید ویژگی (مانند "وزن")
                        value=value  # مقدار ویژگی (مانند "1kg")
                    )
                
                
                
                # ذخیره تصاویر اضافی مرتبط با محصول
                for image_path in additional_images:
                    ProductImage.objects.create(product=product, image=image_path)
                    
                markup = send_menu(message, ProfileModel.objects.get(tel_id=message.from_user.id).tel_menu, message.text, ProfileModel.objects.get(tel_id=message.from_user.id).extra_button_menu)
                self.bot.send_message(message.chat.id, "اطلاعات محصول با موفقیت ثبت شد!", reply_markup=markup)
                self.reset_state(message.chat.id)
            else:
                self.bot.send_message(message.chat.id, f"لطفاً {3 - len(additional_images)} تصویر دیگر ارسال کنید:")
        except Exception as e:
            error_message = traceback.format_exc()
            self.bot.send_message(message.chat.id, f"خطایی رخ داده است: {e}\nجزئیات:\n{error_message}")
            print(error_message)
            

    def delete(self, message: Message):
        try:
            if message.text=="منصرف شدم":
                self.cancle_request(message)
            else:
                code=message.text
                product = Product.objects.get(code=code)
                send_product_message(self.bot, message=message, product=product, current_site='https://intelleum.ir', buttons=False)
                menu = ["بله مطمئنم", "منصرف شدم"]
                markup = send_menu(message, menu, "main menu", home_menu)
                self.bot.send_message(message.chat.id, f"آیا از حذف این کالا اطمینان داری؟", reply_markup=markup)
                self.bot.register_next_step_handler(message, self.delete_sure, product)
                self.reset_state(message.chat.id)
                
        except Product.DoesNotExist:
            self.bot.send_message(message.chat.id, "کالایی با این کد وجود ندارد.")
            return
            
           
    
    def delete_sure(self, message, product):
        try:
            if message.text=="بله مطمئنم":
                product.delete()
                main_menu = ProfileModel.objects.get(tel_id=message.from_user.id).tel_menu
                extra_button_menu = ProfileModel.objects.get(tel_id=message.from_user.id).extra_button_menu
                markup = send_menu(message, main_menu, "main menu", extra_button_menu)
                self.bot.send_message(message.chat.id, f"کالای مورد نظر با موفقیت حذف شد.", reply_markup=markup)
                self.reset_state(message.chat.id)
                
            elif message.text=="منصرف شدم":
                self.cancle_request(message)
                return 
        except Exception as e:
            self.bot.send_message(message.chat.id, "خطایی رخ داده است. لطفاً دوباره تلاش کنید.")
            print(f"Error: {e}")
            
    def cancle_request(self, message):
        if subscription.subscription_offer(message):
            main_menu = ProfileModel.objects.get(tel_id=message.from_user.id).tel_menu
            extra_button_menu = ProfileModel.objects.get(tel_id=message.from_user.id).extra_button_menu
            markup = send_menu(message, main_menu, "main menu", extra_button_menu)
            self.bot.send_message(message.chat.id, "لطفا یکی از گزینه های زیر را انتخاب کنید:", reply_markup=markup)
            self.reset_state(message.chat.id)
            return
            
            
def send_payment_link(app, context):
    chat_id = update.message.chat_id
    email = "example@test.com"  # ایمیل کاربر
    mobile = "09123456789"  # شماره موبایل کاربر
    amount = 100000  # مبلغ پرداخت
    description = "توضیحات کالا"

    # ساخت لینک پرداخت
    payment_url = f"http://intelleum.ir/buy/{amount}/{description}/?email={email}&mobile={mobile}"

    return payment_url