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
async def end_chat(message: Message):
    """پایان چت از طریق پیام"""
    try:
        # ✅ استفاده از SupportChatManager
        SupportChatManager.set_support_mode(message.chat.id, True)
        
        result = await home_handler(message)
        return result
        
    except Exception as e:
        print(f"Error in end_chat: {traceback.format_exc()}")
        error_msg = await message.reply("Opps! A server error occured please contact the administrator.")
        return error_msg


@bot.on_message(condition=create_menu_condition("menu_support"))
@clear_previous_messages(namespace="clear_message")
async def menu_support(message: Message):
    """منوی پشتیبانی"""
    try:
        # ✅ فعال کردن حالت پشتیبانی با SupportChatManager
        SupportChatManager.set_support_mode(message.chat.id, True)
        
        response = await get_profile(message.chat.id)
        markup = await send_menu(message, [await t(message, "end_chat")], "support_chat", profile_response=response)
        
        result = await message.reply(await t(message, "start_support_chat"), reply_markup=markup)
        return result
        
    except Exception as e:
        print(f"Error in menu_support: {traceback.format_exc()}")
        error_msg = await message.reply("Opps! A server error occured please contact the administrator.")
        return error_msg


@bot.on_message(condition=lambda message: SupportChatManager.is_support_mode(message.chat.id))
@store_messages(max_messages=100)
async def question(message: Message):
    """دریافت سوال کاربر در حالت پشتیبانی"""
    try:
        # ارسال پیام به فروشنده (ادمین)
        result1 = await send_question_to_seller(message)
        
        # ارسال پیام تأیید به کاربر
        result2 = await question_send_confirm(message)
        
        # برگرداندن هر دو پیام به صورت لیست
        return [result1, result2]
        
    except Exception as e:
        print(f"Error in question: {traceback.format_exc()}")
        error_msg = await message.reply("Opps! A server error occured please contact the administrator.")
        return error_msg


# ================================================
# هندلر دریافت پاسخ ادمین
# ================================================ 


##################################################
# CART
##################################################


@bot.on_message(condition=create_menu_condition("menu_cart"))
@auto_clear
async def menu_cart(message):
    try:
        response = await get_profile(message.chat.id, url="owned_store")
        result = await message.reply(f"{response}")
        return result
    except:
        error_msg = await message.reply("Opps! A server error occured please contact the administrator.")
        print(f"Opps! An error in {traceback.extract_stack()[-2].name}. \nThe error is: {traceback.format_exc()}")
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

