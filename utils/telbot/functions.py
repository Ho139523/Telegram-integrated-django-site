from utils.variables.TOKEN import TOKEN
import requests
import subprocess


# send_product_message function
from telebot import types




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
    
    
    
def send_product_message(app, message, product, current_site, token):
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
    
    product_code_link = f'`{product.code}`&parse_mode=MarkDown"'
    
    caption = (
        f"\n⭕️ نام کالا: {product.name}\n"
        f"🔖 برند کالا: {product.brand}\n"
        f"کد کالا: {product_code_link}\n\n"
        f"{product.description}\n\n"
        f"✅ {attribute_text}\n\n"
        f"🔘 فروش با ضمانت ارویجینال💯\n"
        f"📫 ارسال به تمام نقاط کشور\n\n"
        f"{price_text}\n"
    )
    
    # Prepare photos
    photos = [
        types.InputMediaPhoto(open(product.main_image.path, 'rb'), caption=caption, parse_mode='MarkdownV2')
    ] + [
        types.InputMediaPhoto(open(i.image.path, 'rb')) for i in product.image_set.all()
    ]
    
    if len(photos) > 10:
        photos = photos[:10]  # Limit to 10 photos
    
    # Create inline keyboard markup
    markup = types.InlineKeyboardMarkup()
    buy_button = types.InlineKeyboardButton(text="خرید", url=f"{current_site}/bbuy/product/{product.code}")
    add_to_basket_button = types.InlineKeyboardButton(text="🛒", url=f"{current_site}/bbuy/product/{product.code}")
    markup.add(add_to_basket_button, buy_button)
    
    # Send product photos and message
    app.send_media_group(message.chat.id, media=photos)
    app.send_message(message.chat.id, "برای خرید یا افزودن کالا به سبد خرید کلیک کیند 👇👇👇", reply_markup=markup)
