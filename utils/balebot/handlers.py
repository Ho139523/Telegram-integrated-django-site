# utils/balebot/handlers.py
import traceback
import logging
from balethon.objects import Message
from utils.balebot.api_client import BaleAPIClient
from utils.balebot.helpers import t
from utils.balebot.helpers import send_menu

logger = logging.getLogger(__name__)

async def language_setting(message: Message):
    """
    First time user setup - language selection
    """
    await message.reply("Welcome to the bot! Please select your language.")
    # TODO: Add language selection logic


##################################
#            HELP
##################################


async def process_help_command(message: Message):
    """
    Handle /help command - show help menu
    """
    help_text = (
        "📚 **Bot Help:**\n\n"
        "/start - Restart the bot\n"
        "/help - Show this help message"
    )
    await message.reply(help_text)


##################################
#            DEFAULT
##################################


async def default_message_handler(message: Message):
    """
    Default handler for unrecognized messages
    """
    await message.reply("❌ I didn't understand that. Please use /help.")



##################################
#            START
##################################


async def process_start_command(message: Message):
    """
    Handle /start command - check registration and route user
    """
    try:
        user = message.author
        user_id = user.id
        bale_username = user.username or ""
        bale_first_name = user.first_name or ""
        bale_last_name = user.last_name or ""
        
        #logger.info(f"Start command from user {user_id}")

        # 1. Send signed request to check registration

        client = BaleAPIClient(base_url="http://127.0.0.1:8000")
        
        # 1. first check if the profile exists or not
        
        check_response = await client._request("POST", "/api/bot/profiles/check/", {"bale_id": user_id})
        
        if check_response.success and check_response.data.get('exists'):
            #print(f"📌 Profile with user_id {user_id} already exists")
            # recieve profile
            get_response = await get_profile(message.chat.id)
            if get_response.success:
                #print(f"Data: {get_response.data.get('data', {})}")
                await home_handler(message)
        else:
            #print(f"📌 Profile with user_id {user_id} not found. Creating new one...")
            # ساخت پروفایل جدید
            create_response = await client._request("POST", "/api/bot/profiles/", {
                "bale_id": user_id,
                "fname": bale_first_name,
                "lname": bale_last_name,
                "bale": bale_username
            })
            
            if create_response.success:
                await language_setting(message)
            else:
                logger.info(f"❌ Creation failed: {create_response.error}")
    
        await client.close()

    except Exception as e:
        logger.error(f"Error in start_handler: {traceback.format_exc()}")
        await message.reply("An error occurred. Please try again later.")


##################################
#            HOME
##################################


from typing import List, Union
from balethon.objects import Message, CallbackQuery
from typing import Optional, Dict, Any
from django.core.cache import cache
from utils.balebot.helpers import t, send_menu
from telbot.sessions import session_manager
from balethon.objects import ReplyKeyboard, ReplyKeyboardButton, Message
from utils.balebot.helpers import get_profile

    

# utils/balebot/handlers.py

from utils.balebot.api_client import BaleAPIClient

async def home_handler(
    event: Union[Message, CallbackQuery], 
    text: Optional[str] = None, 
    session_delete: Optional[List[str]] = None
):
    """
    Main menu handler for Bale bot
    """
    try:
        # استخراج اطلاعات از رویداد
        is_callback = isinstance(event, CallbackQuery)
        
        if is_callback:
            message = event.message
            user_id = message.chat.id
            await event.answer()  # پاسخ به callback
            print(f"Home callback from user {user_id}")
        else:
            message = event
            user_id = message.chat.id
            #print(f"Home message from user {user_id}")
        
        # بررسی اشتراک کاربر (موقتی غیرفعال برای تست)
        # if not subscription.subscription_offer(message):
        #     await message.reply("You don't have an active subscription.")
        #     return
        
        # لیست session‌هایی که باید ریست شوند
        session_list = ["address", "menu", "add_product", "delete_product", "phone", "createshop"]
        
        # ریست کردن session‌ها
        if session_delete:
            sessions_to_reset = [s for s in session_list if s not in session_delete]
            for session_name in sessions_to_reset:
                session_manager.reset_user_session(user_id, namespace=session_name)
        else:
            for session_name in session_list:
                session_manager.reset_user_session(user_id, namespace=session_name)
        
        # دریافت پروفایل کاربر از API
        response = await get_profile(message.chat.id)

        profile_data = response.data.get('data', {})
        
        
        if not profile_data:
            print(f"No profile data for user {user_id}")
            await message.reply("Profile not found. Please use /start to register.")
            return
        
        #print(f"Profile data received: {profile_data.get('fname')} {profile_data.get('lname')}")
        
        # ساخت منو - باید مطمئن شویم که توابع send_menu و t در دسترس هستند
        try:
            
            markup = await send_menu(
                message, 
                profile_data.get('tel_menu'), 
                "main_menu", 
                profile_data.get('extra_button_menu'),
                profile_response=response
            )

            
            # متن پیش‌فرض اگر داده نشده باشد
            if not text:
                # استفاده از نسخه async تابع t
                text = await t(
                    event=message,
                    key="home_message",
                    chat_id=user_id,
                    lang=profile_data.get('lang')
                )
            
            # ارسال پیام
            await message.reply(text, reply_markup=markup)
            #print("Home menu sent successfully")
            
        except Exception as e:
            print(f"Error building menu: {traceback.format_exc()}")
            # Fallback: ارسال پیام ساده بدون منو
            await message.reply("Welcome to the bot! Use /start to see the menu.")
        
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error in home_handler: {e}\n{error_details}")
        await message.reply("An error occurred. Please try again later.")


##################################
#            MENU BALANCE
##################################


from utils.telbot.variables import home_menu

async def menu_balance_handler(message: Message):
    response = await get_profile(message.chat.id)
    options = [await t(message, "my_balance"), await t(message, "increase_balance")]
    markup = await send_menu(message, options, "balance_menu", home_menu, profile_response=response)
    await message.reply(await t(message, "balance_menue"), reply_markup=markup)



