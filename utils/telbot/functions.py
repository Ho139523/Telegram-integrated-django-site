from utils.variables.TOKEN import TOKEN
import requests
import subprocess
import re
from telebot import TeleBot
from telebot.types import Message
from telebot.storage import StateMemoryStorage
from accounts.models import ProfileModel
from products.models import Product, Category

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
    
    
    
def send_product_message(app, message, product, current_site):
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
    attribute_text = "\n✅ ".join([f"{attr.key}: {attr.value}" for attr in attributes])
    
    caption = (
        f"\n⭕️ نام کالا: {product.name}\n"
        f"🔖 برند کالا: {product.brand}\n"
        f"کد کالا: {product.code}\n\n"
        f"{product.description}\n\n"
        f"✅ {attribute_text}\n\n"
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
    
    # Create inline keyboard markup
    markup = types.InlineKeyboardMarkup()
    buy_button = types.InlineKeyboardButton(text="💰 خرید", callback_data='check_website_subscription')
    add_to_basket_button = types.InlineKeyboardButton(text="🛒", url=f"{current_site}/buy/product/{product.code}")
    markup.add(add_to_basket_button, buy_button)
    
    # Send product photos and message
    app.send_media_group(message.chat.id, media=photos)
    app.send_message(message.chat.id, "برای خرید یا افزودن کالا به سبد خرید کلیک کیند 👇👇👇", reply_markup=markup)

############################  CHECK SUBSCRIPTION  ############################

class SubscriptionClass:
    def __init__(self):
        from utils.variables.CHANNELS import my_channels_with_atsign, my_channels_without_atsign
        self.my_channels_with_atsign = my_channels_with_atsign
        self.my_channels_without_atsign = my_channels_without_atsign
        self.current_site = 'https://intelleum.ir'

    def check_subscription(self, user, channels=None):
        if channels is None:
            channels = self.my_channels_with_atsign
        for channel in channels:
            is_member = app.get_chat_member(chat_id=channel, user_id=user)
            if is_member.status in ["kicked", "left"]:
                return False
        return True

    def subscription_offer(self, message):
        channel_markup = types.InlineKeyboardMarkup()
        check_subscription_button = types.InlineKeyboardButton(text='عضو شدم.', callback_data='check_subscription')
        channel_subscription_button = types.InlineKeyboardButton(text='در کانال ما عضو شوید...', url=f"https://t.me/{self.my_channels_without_atsign[0]}")
        group_subscription_button = types.InlineKeyboardButton(text="در گروه ما عضو شوید...", url=f"https://t.me/{self.my_channels_without_atsign[1]}")
        
        channel_markup.add(channel_subscription_button, group_subscription_button)
        channel_markup.add(check_subscription_button)

        if not self.check_subscription(user=message.from_user.id):
            app.send_message(message.chat.id, "برای تایید عضویت خود در گروه و کانال بر روی دکمه‌ها کلیک کنید.", reply_markup=channel_markup)
            return False
        return True

############################  SEND MENU  ############################

subscription = SubscriptionClass()
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
                print(f'Error: {e}')
            
            

    # second layer category
    def handle_subcategory(self, message):
        from utils.telbot.variables import retun_menue
        try:
            if subscription.subscription_offer(message):
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
                    app.send_message(message.chat.id, f"سلام", reply_markup=markup)
                
        except Exception as e:
            print(f'Error: {e}')

############################  ADD PRODUCT  ############################

def download_and_save_image(file_id, bot, upload_path="product_images/"):
    """
    دانلود تصویر از تلگرام و ذخیره در سیستم فایل Django.
    """
    file_info = bot.get_file(file_id)
    file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"
    response = requests.get(file_url)

    if response.status_code == 200:
        # استخراج نام فایل
        file_name = file_info.file_path.split("/")[-1]
        return ContentFile(response.content, name=f"{upload_path}{file_name}")
    return None


class ProductBot:
    def __init__(self, bot: TeleBot):
        self.bot = bot
        self.user_data = {}

    class ProductState:
        NAME = "name"
        SLUG = "slug"
        BRAND = "brand"
        PRICE = "price"
        DISCOUNT = "discount"
        STOCK = "stock"
        IS_AVAILABLE = "is_available"
        CATEGORY = "category"
        DESCRIPTION = "description"
        CODE = "code"
        MAIN_IMAGE = "main_image"
        ADDITIONAL_IMAGES = "additional_images"

    def register_handlers(self):
        """Register message handlers."""
        # self.bot.register_message_handler(self.start, func=lambda message: message.text == "افزودن کالا")
        self.bot.register_message_handler(self.get_name, func=self.is_state(self.ProductState.NAME))
        self.bot.register_message_handler(self.get_slug, func=self.is_state(self.ProductState.SLUG))
        self.bot.register_message_handler(self.get_brand, func=self.is_state(self.ProductState.BRAND))
        self.bot.register_message_handler(self.get_price, func=self.is_state(self.ProductState.PRICE))
        self.bot.register_message_handler(self.get_discount, func=self.is_state(self.ProductState.DISCOUNT))
        self.bot.register_message_handler(self.get_stock, func=self.is_state(self.ProductState.STOCK))
        self.bot.register_message_handler(self.get_is_available, func=self.is_state(self.ProductState.IS_AVAILABLE))
        self.bot.register_message_handler(self.get_category, func=self.is_state(self.ProductState.CATEGORY))
        self.bot.register_message_handler(self.get_description, func=self.is_state(self.ProductState.DESCRIPTION))
        self.bot.register_message_handler(self.get_code, func=self.is_state(self.ProductState.CODE))
        self.bot.register_message_handler(self.get_main_image, func=self.is_state(self.ProductState.MAIN_IMAGE), content_types=["photo"])
        self.bot.register_message_handler(self.get_additional_images, func=self.is_state(self.ProductState.ADDITIONAL_IMAGES), content_types=["photo"])

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
        self.set_state(message.chat.id, self.ProductState.SLUG)
        self.bot.send_message(message.chat.id, "لطفاً یک اسلاگ برای محصول وارد کنید:")

    def get_slug(self, message: Message):
        self.save_user_data(message.chat.id, "slug", message.text)
        self.set_state(message.chat.id, self.ProductState.BRAND)
        self.bot.send_message(message.chat.id, "لطفاً برند محصول را وارد کنید (اختیاری):")

    def get_brand(self, message: Message):
        self.save_user_data(message.chat.id, "brand", message.text)
        self.set_state(message.chat.id, self.ProductState.PRICE)
        self.bot.send_message(message.chat.id, "لطفاً قیمت محصول را وارد کنید:")

    def get_price(self, message: Message):
        try:
            price = float(message.text)
            self.save_user_data(message.chat.id, "price", price)
            self.set_state(message.chat.id, self.ProductState.DISCOUNT)
            self.bot.send_message(message.chat.id, "درصد تخفیف را وارد کنید:")
        except ValueError:
            self.bot.send_message(message.chat.id, "قیمت باید یک عدد باشد!")

    def get_discount(self, message: Message):
        try:
            discount = float(message.text)
            self.save_user_data(message.chat.id, "discount", discount)
            self.set_state(message.chat.id, self.ProductState.STOCK)
            self.bot.send_message(message.chat.id, "موجودی محصول را وارد کنید:")
        except ValueError:
            self.bot.send_message(message.chat.id, "تخفیف باید یک عدد باشد!")

    def get_stock(self, message: Message):
        try:
            stock = int(message.text)
            self.save_user_data(message.chat.id, "stock", stock)
            self.set_state(message.chat.id, self.ProductState.IS_AVAILABLE)
            self.bot.send_message(message.chat.id, "آیا محصول در دسترس است؟ (بله/خیر):")
        except ValueError:
            self.bot.send_message(message.chat.id, "موجودی باید یک عدد صحیح باشد!")

    def get_is_available(self, message: Message):
        is_available = message.text.strip().lower() in ["بله", "yes"]
        self.save_user_data(message.chat.id, "is_available", is_available)
        self.set_state(message.chat.id, self.ProductState.CATEGORY)
        self.bot.send_message(message.chat.id, "لطفاً دسته‌بندی محصول را وارد کنید:")

    def get_category(self, message: Message):
        self.save_user_data(message.chat.id, "category", message.text)
        self.set_state(message.chat.id, self.ProductState.DESCRIPTION)
        self.bot.send_message(message.chat.id, "توضیحات محصول را وارد کنید (اختیاری):")

    def get_description(self, message: Message):
        self.save_user_data(message.chat.id, "description", message.text)
        self.set_state(message.chat.id, self.ProductState.CODE)
        self.bot.send_message(message.chat.id, "لطفاً یک کد یکتا برای محصول وارد کنید:")

    def get_code(self, message: Message):
        self.save_user_data(message.chat.id, "code", message.text)
        self.set_state(message.chat.id, self.ProductState.MAIN_IMAGE)
        self.bot.send_message(message.chat.id, "لطفاً تصویر اصلی محصول را ارسال کنید:")

    def get_main_image(self, message: Message):
        self.save_user_data(message.chat.id, "main_image", message.photo[-1].file_id)
        self.set_state(message.chat.id, self.ProductState.ADDITIONAL_IMAGES)
        self.bot.send_message(message.chat.id, "لطفاً 3 تصویر اضافی برای محصول ارسال کنید:")

    def get_additional_images(self, message: Message):
        try:
            additional_images = self.user_data[message.chat.id].get("additional_images", [])
            file_id = message.photo[-1].file_id

            # دانلود و ذخیره تصویر
            saved_image = download_and_save_image(file_id, self.bot)
            if saved_image:
                additional_images.append(saved_image)  # ذخیره تصویر دانلود شده
                self.save_user_data(message.chat.id, "additional_images", additional_images)

            # بررسی تعداد تصاویر
            if len(additional_images) >= 3:
                # پایان فرآیند
                user_data = self.user_data.get(message.from_user.id, {})
                if user_data:
                    print("User Data:")
                    for key, value in user_data.items():
                        print(f"{key}: {value}")
                else:
                    print("No data found for the user.")
                product = Product.objects.create(
                    name=self.user_data[message.from_user.id]["name"],
                    slug=self.user_data[message.from_user.id]["slug"],
                    brand=self.user_data[message.from_user.id]["brand"],
                    price=self.user_data[message.from_user.id]["price"],
                    discount=self.user_data[message.from_user.id]["discount"],
                    stock=self.user_data[message.from_user.id]["stock"],
                    is_available=self.user_data[message.from_user.id]["is_available"],
                    category=self.user_data[message.from_user.id]["category"],
                    description=self.user_data[message.from_user.id]["description"],
                    main_image=self.user_data[message.from_user.id]["main_image"],  # تصویر اصلی
                    code=self.user_data[message.from_user.id]["code"]
                )

                # ذخیره تصاویر اضافی
                for image in additional_images:
                    ProductImage.objects.create(product=product, image=image)

                self.bot.send_message(message.chat.id, "اطلاعات محصول با موفقیت ثبت شد!")
                print(self.user_data[message.chat.id])  # نمایش یا ذخیره اطلاعات
                self.reset_state(message.chat.id)
            else:
                self.bot.send_message(message.chat.id, f"لطفاً {3 - len(additional_images)} تصویر دیگر ارسال کنید:")
                
        except Exception as e:
            self.bot.send_message(message.chat.id, f"error is: {e}")


