# balebot/views.py
import json
import logging
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from utils.variables.TOKEN import BTOKEN as TOKEN
from utils.balebot.pakage_development.process_update import MyCustomBot
from utils.balebot.handlers import *
from balethon import Client
from utils.balebot.helpers import t, create_menu_condition
from balethon.conditions import private, equals
from balethon.objects import ReplyKeyboard
import traceback
from utils.telbot.functions import t as t_f
from accounts.models import ProfileModel


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
async def start(message):
    """Handle /start command"""
    try:
        await process_start_command(message)
        return
    except:
        await message.reply("Opps! A server error occured please constact the adminstrator.")
        print(f"Opps! An error in {traceback.extract_stack()[-2].name}. \nThe error is: {traceback.format_exc()}")


@bot.on_command("help")
async def help(message):
    """Handle /help command"""
    await process_help_command(message)

	


# ================================================
# Message Handlers
# ================================================


##################################################
# HOME
##################################################


from balethon.objects import Message, CallbackQuery
from utils.balebot.handlers import home_handler

@bot.on_message(condition=lambda message: message.text == "🏡")
async def home_message(message: Message):
    try:
        await home_handler(message)
        return
    except:
        await message.reply("Opps! A server error occured please constact the adminstrator.")
        print(f"Opps! An error in {traceback.extract_stack()[-2].name}. \nThe error is: {traceback.format_exc()}")


@bot.on_callback_query(condition=lambda callback: callback.data in ["🏡"])
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
async def menu_balance(message: Message):
    try:
        await menu_balance_handler(message)
    except:
        await message.reply("Opps! A server error occured please constact the adminstrator.")
        print(f"Opps! An error in {traceback.extract_stack()[-2].name}. \nThe error is: {traceback.format_exc()}")


##################################################
# MENU BUY BY CODE
##################################################


@bot.on_message(condition=create_menu_condition("menu_buy_by_code"))
async def buy_by_code(message: Message):
    try:
        await message.reply(await t(message, "enter_product_code_to_search"))
    except:
        await message.reply("Opps! A server error occured please constact the adminstrator.")
        print(f"Opps! An error in {traceback.extract_stack()[-2].name}. \nThe error is: {traceback.format_exc()}")


##################################################
# HELP
##################################################


@bot.on_message(condition=lambda message: message.text in ["help"])
async def inline_help(message):
    """Handle 'help' text message (without slash)"""
    try:
        await process_help_command(message)
    except:
        await message.reply("Opps! A server error occured please constact the adminstrator.")
        print(f"Opps! An error in {traceback.extract_stack()[-2].name}. \nThe error is: {traceback.format_exc()}")


##################################################
# DEFAULT
##################################################

        
@bot.on_message()
async def default(message):
    try:
        """Default handler for any unmatched message"""
        await default_message_handler(message)
    except:
        await message.reply("Opps! A server error occured please constact the adminstrator.")
        print(f"Opps! An error in {traceback.extract_stack()[-2].name}. \nThe error is: {traceback.format_exc()}")



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

