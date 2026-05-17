# balebot/views.py
import json
import logging
from os import wait
import profile
from unittest import result
from urllib import response
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from utils.variables.TOKEN import BTOKEN as TOKEN
from utils.balebot.pakage_development.process_update import MyCustomBot
from utils.balebot.handlers import *
from balethon import Client
from utils.balebot.helpers import *
from balethon.conditions import private, equals
from balethon.objects import ReplyKeyboard
import traceback
from utils.telbot.functions import t as t_f
from accounts.models import ProfileModel
from utils.telbot.variables import home_menu, retun_menue
from telbot.sessions import session_manager
from utils.balebot.decorators import *


logger = logging.getLogger(__name__)

# ================================================
# Bot Initialization
# ================================================
from utils.balebot.pakage_development.process_update import bot
# bot = Client(TOKEN)

# ================================================
# Command Handlers
# ================================================

@bot.on_command("start")
@clear_previous_messages("clear_message")
async def start(message):
    """Handle /start command"""
    try:
        result = await process_start_command(message)
        return result
    except:
        error_msg = await message.reply("Opps! A server error occured please constact the adminstrator.")
        print(f"Opps! An error in {traceback.extract_stack()[-2].name}. \nThe error is: {traceback.format_exc()}")
        return error_msg


@bot.on_command("help")
@clear_previous_messages("clear_message")
async def help(message):
    """Handle /help command"""
    result = await process_help_command(message)
    return result


# ================================================
# Message Handlers
# ================================================


##################################################
# HOME
##################################################


from balethon.objects import Message, CallbackQuery
from utils.balebot.handlers import home_handler

@bot.on_message(condition=lambda message: message.text == "🏡")
@clear_previous_messages("clear_message")
async def home_message(message: Message):
    try:
        # ✅ نتیجه را برگردان
        result = await home_handler(message)
        return result
    except Exception as e:
        error_msg = await message.reply("Opps! A server error occured please contact the administrator.")
        print(f"Opps! An error in {traceback.extract_stack()[-2].name}. \nThe error is: {traceback.format_exc()}")
        return error_msg
    


@bot.on_callback_query(condition=lambda callback: callback.data in ["🏡"])
@clear_previous_messages("clear_message")
async def home_callback(callback: CallbackQuery):
    """Handle home button callback"""
    try:
        await home_handler(callback)
    except:
        await message.reply("Opps! A server error occured please constact the adminstrator.")
        print(f"Opps! An error in {traceback.extract_stack()[-2].name}. \nThe error is: {traceback.format_exc()}")



##################################################
# MENU BALANCE
##################################################


@bot.on_message(condition=create_menu_condition("menu_balance"))
@clear_previous_messages("clear_message")
async def menu_balance(message: Message):
    try:
        # ✅ نتیجه را برگردان
        result = await menu_balance_handler(message)
        return result
    except Exception as e:
        error_msg = await message.reply("Opps! A server error occured please contact the administrator.")
        print(f"Opps! An error in {traceback.extract_stack()[-2].name}. \nThe error is: {traceback.format_exc()}")
        return error_msg
    

##################################################
# MENU BUY BY CODE
##################################################


@bot.on_message(condition=create_menu_condition("menu_buy_by_code"))
@clear_previous_messages("clear_message")
async def buy_by_code(message: Message):
    try:
        result = await message.reply(await t(message, "enter_product_code_to_search"))
        return result
    except:
        error_msg = await message.reply("Opps! A server error occured please contact the administrator.")
        print(f"Opps! An error in {traceback.extract_stack()[-2].name}. \nThe error is: {traceback.format_exc()}")
        return error_msg


##################################################
# MENU SETTINGS
##################################################


@bot.on_message(condition=create_menu_condition("menu_settings"))
@clear_previous_messages("clear_message")
async def menu_settings(message: Message):
    try:
        response = await get_profile(message.chat.id)
        profile_data = response.data.get("data", {})
        markup = await send_menu(message, profile_data.get("settings_menu"), "settings",
                            home_menu, 2, profile_response=response)
        result = await message.reply(await t(message, "settings_message"), reply_markup=markup)
        return result
    except:
        error_msg = await message.reply("Opps! A server error occured please contact the administrator.")
        print(f"Opps! An error in {traceback.extract_stack()[-2].name}. \nThe error is: {traceback.format_exc()}")
        return error_msg


##################################################
# MENU PROFILE
##################################################


@bot.on_message(condition=create_menu_condition("menu_profile"))
@clear_previous_messages("clear_message")
async def menu_profile(message: Message):
    try:
        response = await get_profile(message.chat.id)
        profile_data = response.data.get("data", {})

        markup = await send_menu(message, profile_data.get("profile_menu"), "settings",
                           home_menu, 2, profile_response=response)
        result = await message.reply(await t(message, "profile_settings"), reply_markup=markup)
        return result
    except:
        error_msg = await message.reply("Opps! A server error occured please contact the administrator.")
        print(f"Opps! An error in {traceback.extract_stack()[-2].name}. \nThe error is: {traceback.format_exc()}")
        return error_msg


##################################################
# MENU LANGUAGE
##################################################


@bot.on_message(condition=create_menu_condition("menu_language"))
@clear_previous_messages("clear_message")
async def menu_profile(message: Message):
    try:
        response = await get_profile(message.chat.id)
        profile_data = response.data.get("data", {})

        
        def get_language_choices():
            language_map = {
                'fa': '🇮🇷 فارسی',
                'en': '🇬🇧  English',
                'zh': '🇨🇳  中国人',
                'ru': '🇷🇺  русский',
                'ar': '🇵🇸  عربیة',
            }
            return [name for code, name in language_map.items()]

        markup = await send_menu(message, get_language_choices(), "language_menu", retun_menue, profile_response=response)
        result = await message.reply(await t(message, "language_setting"), reply_markup=markup)
        return result
    except:
        error_msg = await message.reply("Opps! A server error occured please contact the administrator.")
        print(f"Opps! An error in {traceback.extract_stack()[-2].name}. \nThe error is: {traceback.format_exc()}")
        return error_msg



@bot.on_message(condition=lambda message: message.text in ['🇮🇷 فارسی', '🇬🇧  English', '🇨🇳  中国人', '🇷🇺  русский', '🇵🇸  عربیة',])
@clear_previous_messages("clear_message")
async def change_language(message):
    try:
        session = session_manager.get_user_session(message.chat.id, namespace="menu")
        
        # نگاشت زبان‌ها
        lang_map = {
            '🇮🇷 فارسی': 'fa',
            '🇬🇧  English': 'en',
            '🇨🇳  中国人': 'zh',
            '🇷🇺  русский': 'ru',
            '🇵🇸  عربیة': 'ar'
        }
        
        # پیدا کردن زبان انتخاب شده
        selected_lang = None
        for key, value in lang_map.items():
            if key in message.text:
                selected_lang = value
                break

        if not selected_lang:
            return
        
        # به‌روزرسانی پروفایل
        if session.get("store_lang", None):
            # TODO: به‌روزرسانی زبان فروشگاه
            pass
        else:
            success = await update_profile(message.chat.id, {"lang": selected_lang})
            if not success:
                err_msg = await message.reply("Opps! A server error occured please contact the administrator.")
                return err_msg
        
        
        # ارسال پیام تایید
        text = await t(message, "store_language_changed") if session.get("store_lang", None) else await t(message, "your_lang_changed")
        result = await home_handler(message, text=text)
        return result
        
    except Exception as e:
        error_msg = await message.reply("Opps! A server error occured please contact the administrator.")
        print(f"Opps! An error in {traceback.extract_stack()[-2].name}. \nThe error is: {traceback.format_exc()}")
        return error_msg


##################################################
# MENU BECOME SELLER
##################################################


@bot.on_message(condition=create_menu_condition("menu_become_seller"))
@clear_previous_messages("clear_message")
async def menu_become_seller(message):
    """Redirects you to seller mode and returns seller menu if and only if you have seller account"""
    try:
        result = await menu_become_seller_handler(message)
        return result
    except:
        error_msg = await message.reply("Opps! A server error occured please contact the administrator.")
        print(f"Opps! An error in {traceback.extract_stack()[-2].name}. \nThe error is: {traceback.format_exc()}")
        return error_msg
    

##################################################
# BACK TO BUYER
##################################################


@bot.on_message(condition=create_menu_condition("menu_back_to_buyer"))
@clear_previous_messages("clear_message")
async def back_to_buyer(message):
    """Redirects you to buyer mode and returns buyer menu."""
    try:
        result = await back_to_buyer_handler(message)
        return result
    except:
        error_msg = await message.reply("Opps! A server error occured please contact the administrator.")
        print(f"Opps! An error in {traceback.extract_stack()[-2].name}. \nThe error is: {traceback.format_exc()}")
        return error_msg


##################################################
# MENU SUPPORT
##################################################


@bot.on_message(condition=create_menu_condition("end_chat"))
@clear_messages_on_command()
async def end_chat(message):
    try:

        session = session_manager.get_user_session(message.chat.id, namespace="support chat")
        session["support_mode"] = True
        session_manager.set_user_session(message.chat.id, session, namespace="support chat")
        result = await home_message(message)
        return result
        
    except:
        print(f"Error in question: {traceback.format_exc()}")
        error_msg = await message.reply("Opps! A server error occured please contact the administrator.")
        return error_msg

        

@bot.on_message(condition=create_menu_condition("menu_support"))
@clear_previous_messages(namespace="clear_message")
async def menu_support(message):
    try:
        session = session_manager.get_user_session(message.chat.id, namespace="support chat")
        response = await get_profile(message.chat.id)
        markup = await send_menu(message, [await t(message, "end_chat"),], "support_chat", profile_response=response)
        session["support_mode"] = True
        session_manager.set_user_session(message.chat.id, session, namespace="support chat")
        result = await message.reply(await t(message, "start_support_chat"), reply_markup=markup)
        return result
    except:
        error_msg = await message.reply("Opps! A server error occured please contact the administrator.")
        print(f"Opps! An error in {traceback.extract_stack()[-2].name}. \nThe error is: {traceback.format_exc()}")
        return error_msg
    


@bot.on_message(condition=lambda message: session_manager.get_user_session(message.chat.id, namespace="support chat").get("support_mode"))
@store_messages(max_messages=100)
async def question(message):
    try:
        # ارسال پیام اول به فروشنده
        result1 = await send_question_to_seller(message)
        
        # ارسال پیام تأیید
        result2 = await question_send_confirm(message)
        
        # برگرداندن هر دو پیام به صورت لیست
        return [result1, result2, message]
        
    except Exception as e:
        print(f"Error in question: {traceback.format_exc()}")
        error_msg = await message.reply("Opps! A server error occured please contact the administrator.")
        return error_msg






@bot.on_callback_query(condition=lambda callback: callback.data == "support_reply")
@auto_clear
async def support_reply(callback: CallbackQuery):
    """هندلر پاسخ به پیام کاربر - وقتی ادمین روی دکمه پاسخ کلیک می‌کند"""
    try:

        result = await support_reply_callback(callback)
        return result
        
    except Exception as e:
        print(f"Error in support_reply_callback: {traceback.format_exc()}")
        error_msg = await callback.message.reply("خطا رخ داد")
        return error_msg


@bot.on_callback_query(condition=lambda callback: callback.data == "end_chat")
@auto_clear
async def end_chat_callback(callback: CallbackQuery):
    """هندلر پایان چت - وقتی ادمین یا کاربر روی دکمه پایان کلیک می‌کند"""
    try:
        print("helo")
        await callback.answer()
        message = callback.message
        result = await end_chat(message)
        
        return result
        
    except Exception as e:
        print(f"Error in support_end_chat_callback: {traceback.format_exc()}")
        error_msg = await callback.message.reply("خطا در پایان مکالمه")
        return error_msg


# ================================================
# هندلر پاسخ ادمین (با ForceReply)
# ================================================

# @bot.on_message(condition=lambda message: session_manager.get_user_session(message.chat.id, namespace="support chat").get("support_mode"))
# @store_messages(max_messages=100)
# async def support_reply_handler(message: Message):
#     """
#     هندلر پاسخ پشتیبان - بررسی می‌کند که آیا ادمین در حالت پاسخگویی است
#     و پیام در پاسخ به پیام قبلی ارسال شده است
#     """
#     try:
#         # بررسی اینکه آیا کاربر (ادمین) در حالت پاسخگویی است
#         replying_to = SupportChatManager.get_replying_to(message.chat.id)
        
#         if not replying_to:
#             # در حالت پاسخگویی نیست، ادامه نده
#             return
        
#         # بررسی اینکه پیام در پاسخ به پیام قبلی ارسال شده باشد
#         if not message.reply_to_message:
#             error_msg = await message.reply(await t(message, "reply_to_message_required"))
#             return error_msg
        
#         # استخراج شناسه کاربر از متن پیام
#         user_id = extract_user_id_from_text(message.reply_to_message.text)
        
#         if not user_id:
#             error_msg = await message.reply(await t(message, "user_id_not_found"))
#             SupportChatManager.clear_replying_to(message.chat.id)
#             return error_msg
        
#         # دریافت پیام اصلی کاربر
#         pending_message = SupportChatManager.get_pending_message(user_id)
        
#         # ارسال پاسخ به کاربر اصلی
#         if pending_message:
#             response_text = await t(
#                 message,
#                 "support_reply_with_message",
#                 user_message=pending_message.get("text", ""),
#                 support_answer=message.text
#             )
#         else:
#             response_text = await t(
#                 message,
#                 "support_reply_without_original",
#                 support_answer=message.text
#             )
        
#         # ارسال پاسخ به کاربر
#         await bot.send_message(
#             chat_id=user_id,
#             text=response_text,
#             parse_mode="HTML"
#         )
        
#         # پاک کردن پیام در انتظار پاسخ
#         SupportChatManager.delete_pending_message(user_id)
        
#         # ارسال تأیید به ادمین
#         confirmation_msg = await t(message, "message_sent")
#         result = await message.reply(confirmation_msg)
        
#         # پاک کردن حالت پاسخگویی ادمین
#         SupportChatManager.clear_replying_to(message.chat.id)
        
#         return result
        
#     except Exception as e:
#         print(f"Error in support_reply_handler: {traceback.format_exc()}")
#         error_msg = await message.reply(await t(message, "error_occurred"))
#         return error_msg


# ================================================
# هندلرهای منوی پشتیبانی
# ================================================

@bot.on_message(condition=create_menu_condition("menu_support"))
@clear_previous_messages(namespace="clear_message")
async def menu_support(message: Message):
    """منوی پشتیبانی"""
    try:
        # فعال کردن حالت پشتیبانی برای کاربر
        SupportChatManager.set_support_mode(message.chat.id, True)
        
        response = await get_profile(message.chat.id)
        markup = await send_menu(
            message, 
            [await t(message, "end_chat")], 
            "support_chat", 
            profile_response=response
        )
        
        result = await message.reply(
            await t(message, "start_support_chat"), 
            reply_markup=markup
        )
        return result
        
    except Exception as e:
        print(f"Error in menu_support: {traceback.format_exc()}")
        error_msg = await message.reply("Opps! A server error occured please contact the administrator.")
        return error_msg




# ================================================
# هندلر دریافت پیام کاربر در حالت پشتیبانی
# ================================================

@bot.on_message(condition=lambda message: SupportChatManager.is_support_mode(message.chat.id))
@store_messages(max_messages=100)
async def question(message: Message):
    """دریافت سوال کاربر در حالت پشتیبانی"""
    try:
        # ارسال پیام به فروشنده (ادمین)
        result1 = await send_question_to_seller(message)
        
        # ارسال پیام تأیید به کاربر
        result2 = await question_send_confirm(message)
        
        # برگرداندن هر دو پیام
        return [result1, result2]
        
    except Exception as e:
        print(f"Error in question: {traceback.format_exc()}")
        error_msg = await message.reply("Opps! A server error occured please contact the administrator.")
        return error_msg



##################################################
# HELP
##################################################


@bot.on_message(condition=lambda message: message.text in ["help"])
@clear_previous_messages("clear_message")
async def inline_help(message):
    """Handle 'help' text message (without slash)"""
    try:
        result = await process_help_command(message)
        return result
    except:
        error_msg = await message.reply("Opps! A server error occured please contact the administrator.")
        print(f"Opps! An error in {traceback.extract_stack()[-2].name}. \nThe error is: {traceback.format_exc()}")
        return error_msg


##################################################
# DEFAULT
##################################################

        
@bot.on_message()
@clear_previous_messages("clear_message")
async def default(message):
    try:
        """Default handler for any unmatched message"""
        result = await default_message_handler(message)
        return result
    except:
        error_msg = await message.reply("Opps! A server error occured please contact the administrator.")
        print(f"Opps! An error in {traceback.extract_stack()[-2].name}. \nThe error is: {traceback.format_exc()}")
        return error_msg



# ================================================
# Django Webhook View
# ================================================

@method_decorator(csrf_exempt, name='dispatch')
class BaleBotWebhookView(View):
    """
    Django view to receive webhook updates from Bale messenger
    """

    async def post(self, request, *args, **kwargs):
        try:
            # Parse incoming webhook data
            json_str = request.body.decode('UTF-8')
            data = json.loads(json_str)
            logger.info("Webhook received")

            # Process update with custom bot
            await bot.process_update(data)

            return JsonResponse({"status": "success"}, status=200)

        except Exception as e:
            logger.error(f"Error processing webhook: {e}", exc_info=True)
            return JsonResponse({"status": "error"}, status=200)

