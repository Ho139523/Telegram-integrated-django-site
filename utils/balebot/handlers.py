# utils/balebot/handlers.py
import re
import traceback
import logging
from unittest import result
from balethon.objects import Message
from utils.balebot.api_client import BaleAPIClient
from utils.balebot.helpers import t
from utils.balebot.helpers import *
from utils.telbot.variables import home_menu, retun_menue
from AI.settings import SITE_DOMAIN


logger = logging.getLogger(__name__)
client = BaleAPIClient(base_url="http://127.0.0.1:8000")

async def language_setting(message: Message):
    """
    First time user setup - language selection
    """
    try:
        def get_language_choices():
            language_map = {
                'fa': '🇮🇷 فارسی',
                'en': '🇬🇧  English',
                'zh': '🇨🇳  中国人',
                'ru': '🇷🇺  русский',
                'ar': '🇵🇸  عربیة',
            }
            return [name for code, name in language_map.items()]
        
        markup = await send_menu(
            message, 
            get_language_choices(),
            "language_menu",
            retun_menue,
            profile_response = await get_profile(message.chat.id)
        )
        
        result = await message.reply(await t(message, "language_setting"), reply_markup=markup)
        return result
    except Exception as e:
        error_msg = await message.reply("Opps! A server error occured please contact the administrator.")
        print(f"Opps! An error in {traceback.extract_stack()[-2].name}. \nThe error is: {traceback.format_exc()}")
        return error_msg


##################################
#            HELP
##################################


async def process_help_command(message: Message):
    """
    Handle /help command - show help menu
    """
    try:
        help_text = (
            "📚 **Bot Help:**\n\n"
            "/start - Restart the bot\n"
            "/help - Show this help message"
        )
        result = await message.reply(help_text)
        return result
    except:
        error_msg = await message.reply("Opps! A server error occured please contact the administrator.")
        print(f"Opps! An error in {traceback.extract_stack()[-2].name}. \nThe error is: {traceback.format_exc()}")
        return error_msg


##################################
#            DEFAULT
##################################


async def default_message_handler(message: Message):
    """
    Default handler for unrecognized messages
    """
    try:
        result = await message.reply("❌ I didn't understand that. Please use /help.")
        return result
    except:
        error_msg = await message.reply("Opps! A server error occured please contact the administrator.")
        print(f"Opps! An error in {traceback.extract_stack()[-2].name}. \nThe error is: {traceback.format_exc()}")
        return error_msg



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

        
        # 1. first check if the profile exists or not
        
        check_response = await client._request("POST", "/myapi/profiles/check/", {"bale_id": user_id})
        print(check_response)
        
        if check_response.success and check_response.data.get('exists'):
            #print(f"📌 Profile with user_id {user_id} already exists")
            # recieve profile
            get_response = await get_profile(message.chat.id)
            if get_response.success:
                result = await home_handler(message)
                return result
        else:
            #print(f"📌 Profile with user_id {user_id} not found. Creating new one...")
            # ساخت پروفایل جدید
            create_response = await client._request("POST", "/myapi/profiles/", {
                "bale_id": user_id,
                "fname": bale_first_name,
                "lname": bale_last_name,
                "bale": bale_username,
                "server_store_id": 2,
                "lang": "fa",
            })
            
            if create_response.success:
                result = await language_setting(message)
                return result
            else:
                logger.info(f"❌ Creation failed: {create_response.error}")
    
        

    except Exception as e:
        error_msg = await message.reply("Opps! A server error occured please contact the administrator.")
        print(f"Opps! An error in {traceback.extract_stack()[-2].name}. \nThe error is: {traceback.format_exc()}")
        return error_msg


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
    session_delete: Optional[List[str]] = None,
    *args,
    **kwargs
):
    """
    Main menu handler for Bale bot
    Returns: MessageResult or None
    """
    try:
        # استخراج اطلاعات از رویداد
        is_callback = isinstance(event, CallbackQuery)
        
        if is_callback:
            message = event.message
            user_id = message.chat.id
            await event.answer()
            print(f"Home callback from user {user_id}")
        else:
            message = event
            user_id = message.chat.id
        
        # لیست session‌هایی که باید ریست شوند
        session_list = ["address", "menu", "add_product", "delete_product", "phone", "createshop", "support chat", "clear_message"]
        
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
        
        
        if not response.success or not response.data.get('data'):
            print(f"No profile data for user {user_id}")
            return response
        
        profile_data = response.data.get('data', {})
        
        # ساخت منو
        markup = await send_menu(
            message, 
            profile_data.get('tel_menu'), 
            "main_menu", 
            profile_data.get('extra_button_menu'),
            profile_response=response
        )
        
        # متن پیش‌فرض اگر داده نشده باشد
        if not text:
            text = await t(
                event=message,
                key="home_message",
                chat_id=user_id,
                lang=profile_data.get('lang')
            )
        
        # ✅ ارسال پیام و برگرداندن نتیجه
        result = await message.reply(text, reply_markup=markup)
        return result
        
    except Exception as e:
        error_msg = await message.reply("Opps! A server error occured please contact the administrator.")
        print(f"Opps! An error in {traceback.extract_stack()[-2].name}. \nThe error is: {traceback.format_exc()}")
        return error_msg

##################################
#            MENU BALANCE
##################################


async def menu_balance_handler(message: Message):
    """Handler for balance menu"""
    try:
        response = await get_profile(message.chat.id)
        options = [await t(message, "my_balance"), await t(message, "increase_balance")]
        markup = await send_menu(message, options, "balance_menu", home_menu, profile_response=response)
        
        # ✅ ارسال پیام و برگرداندن نتیجه
        result = await message.reply(await t(message, "balance_menue"), reply_markup=markup)
        return result
        
    except Exception as e:
        error_msg = await message.reply("Opps! A server error occured please contact the administrator.")
        print(f"Opps! An error in {traceback.extract_stack()[-2].name}. \nThe error is: {traceback.format_exc()}")
        return error_msg


##################################
#            MENU BECOME SELLER
##################################


async def menu_become_seller_handler(message: Message):
    """Handler for balance become seller"""
    try:
        success = await update_profile(message.chat.id, {"seller_mode": True})
        if not success:
            err_msg = await message.reply("Opps! A server error occured please contact the administrator.")
            return err_msg
        
        # ✅ ارسال پیام و برگرداندن نتیجه
        result = await home_handler(message)
        return result
        
    except Exception as e:
        error_msg = await message.reply("Opps! A server error occured please contact the administrator.")
        print(f"Opps! An error in {traceback.extract_stack()[-2].name}. \nThe error is: {traceback.format_exc()}")
        return error_msg
    

##################################
#            BACK TO BUYER
##################################


async def back_to_buyer_handler(message: Message):
    """Handler for back to buyer"""
    try:
        success = await update_profile(message.chat.id, {"seller_mode": False})
        if not success:
            err_msg = await message.reply("Opps! A server error occured please contact the administrator.")
            return err_msg
        
        # ✅ ارسال پیام و برگرداندن نتیجه
        result = await home_handler(message)
        return result
        
    except Exception as e:
        error_msg = await message.reply("Opps! A server error occured please contact the administrator.")
        print(f"Opps! An error in {traceback.extract_stack()[-2].name}. \nThe error is: {traceback.format_exc()}")
        return error_msg
    


##################################
#            SUPPORT
##################################

# async def send_question_to_seller(message):
#     buttons = {
#     await t(message, "reply"): {"callback_data": "reply", "index": 1},
#     await t(message, "end_chat"): {"callback_data": "end_chat", "index": 2},
#     }

#     handlers = {
#         "reply": home_handler,
#         "end_chat": home_handler
#     }
    
#     username = message.author.username or await t(message, "without_username")

#     text = await t(
#         message, 
#         "user_message_received", 
#         user_id=message.chat.id, 
#         username=username,
#         text=message.text
#     )

#     clean_text = strip_html_tags(text)
    

#     markup  = SendMarkup(
#         bot=bot,
#         chat_id=message.chat.id,
#         text=clean_text,
#         buttons=buttons,
#         button_layout=[2],
#         handlers=handlers,
#         message=message
#     )

#     result = await markup.send()
#     return result


# async def question_send_confirm(message):
#     buttons = {
#     await t(message, "end_chat"): {"callback_data": "end_chat", "index": 2},
#     }

#     handlers = {
#         "end_chat": home_handler,
#     }

#     text = await t(message, "message_sent")

#     markup  = SendMarkup(
#         bot=bot,
#         chat_id=message.chat.id,
#         text=text,
#         buttons=buttons,
#         button_layout=[1],
#         handlers=handlers,
#         message=message
#     )

#     result = await markup.send()
#     return result


from bs4 import BeautifulSoup
import re
from typing import Dict
from utils.balebot.helpers import SendMarkup
from utils.balebot.ClassBase import *
from utils.balebot.ClassBase import ForceReply




from bs4 import BeautifulSoup
import re
import traceback
from typing import Optional
from balethon.objects import Message, CallbackQuery
from utils.balebot.helpers import SendMarkup, t, get_profile, bot
from utils.balebot.ClassBase import SupportChatManager, ForceReply
from utils.balebot.decorators import store_messages, clear_previous_messages, clear_messages_on_command, auto_clear
from telbot.sessions import session_manager


def extract_user_id_from_text(text: str, pattern: str = None) -> Optional[int]:
    """استخراج شناسه کاربر از متن"""
    try:
        clean_text = BeautifulSoup(text, "html.parser").get_text()
        normalized_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        if pattern:
            match = re.search(pattern, normalized_text)
            if match:
                numbers = re.findall(r"\d+", match.group())
                if numbers:
                    return int(numbers[0])
        
        # جستجوی مستقیم اعداد
        all_numbers = re.findall(r"\d+", normalized_text)
        if all_numbers:
            return int(all_numbers[0])
        
        return None
    except Exception:
        return None


async def send_question_to_seller(message: Message):
    """ارسال سوال کاربر به فروشنده (ادمین)"""
    buttons = {
        await t(message, "reply"): {"callback_data": "support_reply", "index": 1},
        await t(message, "end_chat"): {"callback_data": "support_end_chat", "index": 2},
    }

    handlers = {
        "support_reply": support_reply_callback,
        "support_end_chat": support_end_chat_callback
    }
    
    username = message.author.username or await t(message, "without_username")
    
    # ✅ استفاده از SupportChatManager برای ذخیره پیام کاربر
    SupportChatManager.store_pending_message(
        message.chat.id, 
        message.text, 
        message.message_id
    )

    text = await t(
        message, 
        "user_message_received", 
        user_id=message.chat.id, 
        username=username,
        text=message.text
    )

    # حذف تگ‌های HTML (بله از HTML پشتیبانی نمی‌کند)
    clean_text = BeautifulSoup(text, "html.parser").get_text()

    markup = SendMarkup(
        bot=bot,
        chat_id=message.chat.id,
        text=clean_text,
        buttons=buttons,
        button_layout=[2],
        handlers=handlers,
        message=message
    )

    result = await markup.send()
    return result


async def question_send_confirm(message: Message):
    """ارسال پیام تأیید به کاربر"""
    buttons = {
        await t(message, "end_chat"): {"callback_data": "support_end_chat", "index": 1},
    }

    handlers = {
        "support_end_chat": support_end_chat_callback,
    }

    text = await t(message, "message_sent")

    markup = SendMarkup(
        bot=bot,
        chat_id=message.chat.id,
        text=text,
        buttons=buttons,
        button_layout=[1],
        handlers=handlers,
        message=message
    )

    result = await markup.send()
    return result


@bot.on_callback_query(condition=lambda callback: callback.data == "support_reply")
@auto_clear
async def support_reply_callback(callback: CallbackQuery):
    """هندلر پاسخ به پیام کاربر - وقتی ادمین روی دکمه پاسخ کلیک می‌کند"""
    try:
        await callback.answer()
        
        message = callback.message
        
        # استخراج شناسه کاربر از متن پیام
        user_id = extract_user_id_from_text(message.text)
        
        if not user_id:
            error_msg = await message.reply(await t(message, "user_id_not_found"))
            return error_msg
        
        # ✅ تنظیم حالت پاسخگویی برای ادمین با SupportChatManager
        SupportChatManager.set_replying_to(message.chat.id, user_id)
        
        # ارسال پیام با ForceReply
        text = await t(message, "send_answer_to", user_id=user_id)
        
        result = await message.reply(
            text, 
            reply_markup=ForceReply(),
            parse_mode="HTML"
        )
        
        return result
        
    except Exception as e:
        print(f"Error in support_reply_callback: {traceback.format_exc()}")
        error_msg = await callback.message.reply("خطا رخ داد")
        return error_msg


@bot.on_callback_query(condition=lambda callback: callback.data == "support_end_chat")
@auto_clear
async def support_end_chat_callback(callback: CallbackQuery):
    """هندلر پایان چت - وقتی ادمین یا کاربر روی دکمه پایان کلیک می‌کند"""
    try:
        await callback.answer()
        
        message = callback.message
        
        # ✅ پاک کردن سشن پشتیبانی با SupportChatManager
        SupportChatManager.clear_support_session(message.chat.id)
        SupportChatManager.clear_replying_to(message.chat.id)
        
        text = await t(message, "conversation_ended")
        result = await message.reply(text)
        
        # ✅ غیرفعال کردن حالت پشتیبانی
        SupportChatManager.set_support_mode(message.chat.id, False)
        
        # بازگشت به منوی اصلی
        await home_handler(message)
        
        return result
        
    except Exception as e:
        print(f"Error in support_end_chat_callback: {traceback.format_exc()}")
        error_msg = await callback.message.reply("خطا در پایان مکالمه")
        return error_msg


##################################
#            BUY BY CODE
##################################
from utils.telbot.functions import measure_performance
import time

async def product_code_handler(message):
    try:
        chat_id = message.chat.id
        code = message.text.strip()

        is_valid_code = re.match(r'^\d{10}$', message.text)

        if is_valid_code:
            url = f"/myapi/products/{code}/"
            response = await client._request(method="GET", endpoint=url)
            if response.success and response.data:
                product = response.data
            else:
                product = None

            if not product:
                return await message.reply(await t(message, "product_not_found"))

            if not product.get('status', True):
                return await message.reply(
                    await t(message, "product_disabled_by_seller")
                )

            category = product.get('category')
            if category and isinstance(category, dict):
                if not category.get('status', True):
                    return await message.reply(
                        await t(
                            message,
                            "category_disabled_by_seller",
                            category_title=category.get('title')
                        )
                    )

            product_handler = ProductHandler(
                bot,
                product,
                SITE_DOMAIN,
                attributes=product.get('attributes', []),
            )

            success = await product_handler.send_product_message(message, buttons=True)

            if not success:
                await message.reply(
                    "Failed to send product. Please try again."
                )
                return False

            return success

        else:
            return await message.reply(
                await t(message, "invalid_code")
            )

    except Exception as e:
        error_msg = await message.reply(
            "Oops! A server error occurred. Please contact the administrator."
        )
        print(f"Error details: {traceback.format_exc()}")
        return error_msg
