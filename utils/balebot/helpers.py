# utils/balebot/helpers.py

######################################     T function    ######################################


import traceback
from typing import Union, Optional
from balethon.objects import Message, CallbackQuery
from utils.variables.translate import translations
from utils.balebot.api_client import BaleAPIClient
from utils.telbot.functions import t as t_function
from asgiref.sync import async_to_sync, sync_to_async

async def get_user_lang(chat_id: int) -> str:
    """دریافت زبان کاربر با کش"""
    
    # from accounts.models import ProfileModel
    # profile = ProfileModel.objects.get(bale_id=chat_id)
    # lang = profile.lang
    response = await get_profile(chat_id)
    ppp = response.data.get('data', {})
    print(ppp.get("lang"))
    return ppp.get("lang")


async def t(
    event,  # بدون type hint
    key: str, 
    chat_id: Optional[int] = None, 
    lang: Optional[str] = None, 
    **kwargs
) -> str:
    """نسخه async تابع ترجمه"""
    try:
        if chat_id is None and event:
            if hasattr(event, 'message') and hasattr(event.message, 'chat'):
                chat_id = event.message.chat.id
            elif hasattr(event, 'chat'):
                chat_id = event.chat.id
        
        if lang is None and chat_id:
            # ✅ استفاده از sync_to_async برای فراخوانی ORM
            lang = await get_user_lang(chat_id)
            print(f"Language for {chat_id}: {lang}")
        
        if lang is None:
            lang = "fa"
        
        text = translations.get(key, {}).get(lang, translations.get(key, {}).get("en", key))
        
        if kwargs:
            try:
                text = text.format(**kwargs)
            except:
                pass
        
        return text
        
    except Exception as e:
        print(f"Translation error: {traceback.format_exc()}")
        return key


def create_menu_condition(translation_key: str):
    """
    تابع سازنده شرط منو
    Args:
        translation_key: کلید ترجمه (مثل "menu_balance", "menu_buy", "menu_profile")
    Returns:
        تابع شرط async
    """
    async def condition(message):
        # دریافت زبان کاربر
        user_lang = await get_user_lang(message.chat.id)
        # دریافت متن مورد انتظار با کلید ترجمه پویا
        expected_text = await t(message, translation_key, lang=user_lang)
        return message.text == expected_text
    
    return condition


######################################     SENDMENU    ######################################


from balethon.objects import ReplyKeyboard, ReplyKeyboardButton, Message
from typing import List, Optional
  

async def send_menu(
    message: Message,
    options: List[str],
    current_menu: str,
    extra_buttons: Optional[List[str]] = None,
    cols: int = 3,
    extra_cols: int = 2,
    profile_response = None
) -> ReplyKeyboard:
    """
    Send a reply keyboard menu for Bale bot (shown instead of main keyboard)

    Args:
        message: Balethon Message object
        options: List of menu option keys
        current_menu: Name of current menu (for session tracking)
        extra_buttons: Optional extra buttons (like cart)
        cols: Number of columns for main buttons
        extra_cols: Number of columns for extra buttons

    Returns:
        ReplyKeyboard
    """
    
    # ================================================
    # ساخت دکمه‌های اصلی (ReplyKeyboard)
    # ================================================
    keyboard = []

    if not profile_response:
        user_id = message.chat.id
        client = BaleAPIClient(base_url="http://127.0.0.1:8000")
        profile_response = await client._request("GET", f"/api/bot/profiles/{user_id}/")
        
        if not profile_response.success:
            print(f"API Error: {profile_response.error}")
            await message.reply("Profile not found. Please use /start to register.")
            return
            
    profile_data = profile_response.data.get('data', {})

    # ردیف‌های دکمه‌های اصلی
    for i in range(0, len(options), cols):
        row = options[i:i + cols]
        button_row = []

        for key in row:
            # 🔑 استفاده از تابع t برای ترجمه
            button_text = await t(
                event=message,
                key=key,
                chat_id=message.chat.id,
                lang=profile_data.get("lang")
            )
            
            button_row.append(ReplyKeyboardButton(text=button_text))

        keyboard.append(button_row)

    # ================================================
    # ساخت دکمه‌های اضافی
    # ================================================
    if extra_buttons:
        for i in range(0, len(extra_buttons), extra_cols):
            row = extra_buttons[i:i + extra_cols]
            button_row = []

            for key in row:
                # 🔑 استفاده از تابع t برای ترجمه
                button_text = await t(
                    event=message,
                    key=key,
                    chat_id=message.chat.id,
                    lang=profile_data.get("lang")
                )
                button_row.append(ReplyKeyboardButton(text=button_text))

            keyboard.append(button_row)



    # resize_keyboard=True باعث می‌شود دکمه‌ها کوچک شوند
    # one_time_keyboard=False باعث می‌شود صفحه کلید بعد از کلیک مخفی نشود
    return ReplyKeyboard(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )




#################### GET PROFILE DATA ###########


from utils.balebot.pakage_development.process_update import bot

async def get_profile(user_id):
    
    client = BaleAPIClient(base_url="http://127.0.0.1:8000")
    response = await client._request("GET", f"/api/bot/profiles/{user_id}/")
        
    if not response.success:
        print(f"API Error: {response.error}")
        await bot.send_message(user_id, "Profile not found. Please use /start to register.")
        return
        

    return response




#################### HANDLER CONDITION ###########

# balebot/views.py
from accounts.models import ProfileModel
import traceback


async def handler_text_condition(message: Message, key):

    try:
        
        profile = await get_profile(message.chat.id)
        print(profile)
        print(type(profile))
        text = t_function(
            msg=message,
            key=key,
            lang=profile.get("lang")
        )
        return message.text == text
    except Exception as e:
        print(f"Error in handler_condition: {traceback.format_exc()}")
        return False
