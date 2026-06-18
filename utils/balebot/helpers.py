# utils/balebot/helpers.py

######################################     T function    ######################################


import traceback
from typing import Union, Optional
from balethon.objects import Message, CallbackQuery
from matplotlib.image import resample
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
            # print(f"Language for {chat_id}: {lang}")
        
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
            result = await message.reply("Profile not found. Please use /start to register.")
            return result
            
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


######################################     SENDMARKUP    ######################################


# utils/balebot/markup_builder.py
import traceback
from typing import List, Dict, Any, Optional, Union, Callable
from balethon import Client
from balethon.objects import InlineKeyboard, InlineKeyboardButton
from balethon.objects import Message, CallbackQuery
import asyncio


class SendMarkup:
    """
    کلاس ساخت و ارسال منوهای شیشه‌ای در Balethon
    شبیه‌سازی شده از نسخه Telebot
    """
    
    def __init__(
        self, 
        bot: Client, 
        chat_id: int, 
        text: str = None, 
        buttons: Union[List, Dict] = None, 
        button_layout: List[int] = None, 
        handlers: Dict[str, Callable] = None, 
        message: Message = None
    ):
        self.bot = bot
        self.chat_id = chat_id
        self.text = text
        self.buttons = buttons or []
        self.button_layout = button_layout or []
        self.handlers = handlers or {}
        self._keyboard_cache = None
        self.message = message

    def _validate_button(self, text: str, callback_data: str, is_url: bool = False) -> tuple:
        """اعتبارسنجی دکمه قبل از ساخت"""
        if not text or not isinstance(text, str) or text.strip() == "":
            return False, "متن دکمه نمی‌تواند خالی باشد"
        
        if not is_url and (not callback_data or callback_data.strip() == ""):
            return False, "callback_data نمی‌تواند خالی باشد"
            
        if not isinstance(callback_data, str):
            return False, "callback_data باید رشته باشد"
            
        return True, "معتبر"

    def _convert_buttons_to_list(self) -> List[tuple]:
        """تبدیل دکمه‌ها به فرمت لیست یکپارچه با اعتبارسنجی"""
        if not self.buttons:
            return []
            
        button_list = []
        
        try:
            if isinstance(self.buttons, list):
                for item in self.buttons:
                    if len(item) >= 3:
                        text, callback_data, index = item[0], item[1], item[2]
                        is_valid, message = self._validate_button(text, callback_data)
                        if is_valid:
                            button_list.append((text, callback_data, index))
                        else:
                            print(f"دکمه نامعتبر حذف شد: {text} - {message}")
                    else:
                        print(f"فرمت دکمه نامعتبر: {item}")
            
            elif isinstance(self.buttons, dict):
                for text, button_data in self.buttons.items():
                    callback_data = ""
                    url = ""
                    index = len(button_list) + 1
                    
                    if isinstance(button_data, dict):
                        callback_data = button_data.get('callback_data', '')
                        url = button_data.get('url', '')
                        index = button_data.get('index', index)
                        
                        if url:
                            callback_data = url
                    elif isinstance(button_data, (list, tuple)) and len(button_data) >= 2:
                        callback_data, index = button_data[0], button_data[1]
                    else:
                        print(f"فرمت دکمه نامعتبر برای {text}: {button_data}")
                        continue
                    
                    if url:
                        if not text or not isinstance(text, str) or text.strip() == "":
                            print(f"دکمه نامعتبر حذف شد: {text}")
                            continue
                        button_list.append((text, url, index))
                    else:
                        is_valid, msg = self._validate_button(text, callback_data)
                        if is_valid:
                            button_list.append((text, callback_data, index))
                        else:
                            print(f"دکمه نامعتبر حذف شد: {text} - {msg}")
            
            else:
                print(f"فرمت buttons نامعتبر: {type(self.buttons)}")
                
        except Exception as e:
            print(f"خطا در تبدیل دکمه‌ها: {traceback.format_exc()}")
            
        return button_list

    def generate_keyboard(self) -> InlineKeyboard:
        """ساخت کیبورد با اعتبارسنجی کامل"""
        if self._keyboard_cache:
            return self._keyboard_cache
        
        if not self.buttons:
            return InlineKeyboard()
        
        button_list = self._convert_buttons_to_list()
        
        if not button_list:
            print("هیچ دکمه معتبری برای نمایش وجود ندارد")
            return InlineKeyboard()
        
        try:
            sorted_buttons = sorted(button_list, key=lambda x: x[2])
        except Exception as e:
            print(f"Opps! An error in {traceback.extract_stack()[-2].name}. \nThe error is: {traceback.format_exc()}")
            sorted_buttons = button_list
        
        # ساخت دکمه‌ها
        inline_buttons = []
        for text, callback_data, _ in sorted_buttons:
            try:
                if callback_data.startswith(('http://', 'https://')):
                    inline_buttons.append(InlineKeyboardButton(text=text, url=callback_data))
                else:
                    inline_buttons.append(InlineKeyboardButton(text=text, callback_data=callback_data))
            except Exception as e:
                print(f"Opps! An error in {traceback.extract_stack()[-2].name}. \nThe error is: {traceback.format_exc()}")

                continue
        
        if not inline_buttons:
            print("هیچ دکمه اینلاین معتبری ساخته نشد")
            return InlineKeyboard()
        
        # ساخت InlineKeyboard
        keyboard = InlineKeyboard()
        
        try:
            index = 0
            for row_size in self.button_layout:
                if index >= len(inline_buttons):
                    break
                    
                if row_size <= 0:
                    print(f"سایز ردیف نامعتبر: {row_size}")
                    continue
                    
                row_buttons = inline_buttons[index:index + row_size]
                if row_buttons:
                    keyboard.add_row(*row_buttons)
                index += row_size
                
            if index < len(inline_buttons):
                remaining_buttons = inline_buttons[index:]
                keyboard.add_row(*remaining_buttons)
                
        except Exception as e:
            print(f"Opps! An error in {traceback.extract_stack()[-2].name}. \nThe error is: {traceback.format_exc()}")
            
        self._keyboard_cache = keyboard
        return self._keyboard_cache

    # در کلاس SendMarkup

    async def send(self, parse_mode: str = "HTML") -> Optional[Message]:
        """ارسال پیام با هندل خطا"""
        try:
            markup = self.generate_keyboard()
            
            if hasattr(self.bot, 'send_message_direct'):
                result = await self.bot.send_message_direct(
                    chat_id=self.chat_id,
                    text=self.text,
                    reply_markup=markup,
                    parse_mode=parse_mode
                )
                from utils.balebot.pakage_development.process_update import MessageResult
                message_id = None
                if result and isinstance(result, dict):
                    if result.get('result') and isinstance(result['result'], dict):
                        message_id = result['result'].get('message_id')
                    elif result.get('message_id'):
                        message_id = result.get('message_id')
                return MessageResult(message_id)
            else:
                result = await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=self.text,
                    reply_markup=markup,
                    options={"parse_mode": parse_mode}
                )
                return result
                
        except Exception as e:
            print(f"Error in SendMarkup.send: {traceback.format_exc()}")
            try:
                if hasattr(self.bot, 'send_message_direct'):
                    result = await self.bot.send_message_direct(
                        chat_id=self.chat_id,
                        text=self.text,
                        parse_mode=parse_mode
                    )
                    return result
                else:
                    result = await self.bot.send_message(
                        chat_id=self.chat_id,
                        text=self.text,
                        options={"parse_mode": parse_mode}
                    )
                    return result
            except Exception as e2:
                print(f"Error sending without buttons: {e2}")
                return None

    async def edit(self, message_id: int) -> bool:
        """ویرایش هوشمند پیام"""
        try:
            markup = self.generate_keyboard()
            
            if self.message and hasattr(self.message, 'photo') and self.message.photo:
                await self.bot.edit_message_caption(
                    chat_id=self.chat_id,
                    message_id=message_id,
                    caption=self.text,
                    reply_markup=markup,
                    parse_mode="HTML"
                )
            else:
                if hasattr(self.bot, "edit_message_text_direct"):

                    await self.bot.edit_message_text_direct(
                        chat_id=self.chat_id,
                        message_id=message_id,
                        text=self.text,
                        reply_markup=markup,
                    )
                
                else:
                
                    await self.bot.edit_message_text(
                        chat_id=self.chat_id,
                        message_id=message_id,
                        text=self.text,
                        reply_markup=markup,
                    ) 
            return True
        except Exception as e:
            if "message is not modified" not in str(e):
                print(f"Error in SendMarkup.edit: {traceback.format_exc()}")
            return False

    async def handle_callback(self, callback: CallbackQuery):
        """مدیریت کلیک روی دکمه‌ها"""
        callback_data = callback.data
        if callback_data in self.handlers:
            try:
                handler = self.handlers[callback_data]
                if asyncio.iscoroutinefunction(handler):
                    await handler(callback)
                else:
                    handler(callback)
                await callback.answer()
            except Exception as e:
                print(f"Error in handler for {callback_data}: {traceback.format_exc()}")
                await callback.answer("خطا رخ داد", show_alert=True)

    @staticmethod
    def debug_buttons(buttons):
        """تابع کمکی برای دیباگ دکمه‌ها"""
        print("=== DEBUG BUTTONS ===")
        
        if not buttons:
            print("دکمه‌ها خالی هستند")
            return
        
        if isinstance(buttons, list):
            print(f"فرمت: لیست ({len(buttons)} آیتم)")
            for i, item in enumerate(buttons):
                print(f"  {i}: {item}")
        elif isinstance(buttons, dict):
            print(f"فرمت: دیکشنری ({len(buttons)} آیتم)")
            for key, value in buttons.items():
                print(f"  '{key}': {value}")
        else:
            print(f"فرمت نامشخص: {type(buttons)}")
        
        print("=====================")


# تابع کمکی
async def send_markup(
    bot: Client,
    chat_id: int,
    text: str,
    buttons: Union[List, Dict] = None,
    button_layout: List[int] = None,
    handlers: Dict[str, Callable] = None,
    message: Message = None
) -> SendMarkup:
    """تابع کمکی برای ارسال سریع منو"""
    markup_builder = SendMarkup(
        bot=bot,
        chat_id=chat_id,
        text=text,
        buttons=buttons,
        button_layout=button_layout,
        handlers=handlers,
        message=message
    )
    await markup_builder.send()
    return markup_builder

###################################     GET PROFILE DATA    ###################################

from utils.balebot.pakage_development.process_update import bot

async def get_profile(user_id, url=None):
    try:
    
        client = BaleAPIClient(base_url="http://127.0.0.1:8000")
        url = f"/myapi/profiles/{user_id}/"
        response = await client._request("GET", url)
            
        if not response.success:
            print(f"API Error: {response.error}")
            await bot.send_message(user_id, "Profile not found. Please use /start to register.")
            return
            

        return response

    except:
        print(traceback.format_exc())



async def update_profile(user_id: str, update_data: dict) -> dict:
    """
    به‌روزرسانی پروفایل کاربر با شناسه (tel_id یا bale_id)
    
    Args:
        user_id: شناسه کاربر (tel_id یا bale_id)
        update_data: دیکشنری شامل فیلدهایی که می‌خواهید تغییر دهید
    
    Returns:
        response: پاسخ API شامل پروفایل به‌روز شده
    
    Example:
        update_data = {
            "fname": "نام جدید",
            "lang": "en",
            "phone": "09123456789"
        }
    """
    try:
        client = BaleAPIClient(base_url="http://127.0.0.1:8000")
        response = await client.patch(
            endpoint=f"/api/bot/profiles/{user_id}/",
            payload=update_data
        )
        
        if response.success:
            return response.data
        else:
            print(f"API Error: {response.error}, Status: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Exception in update_profile: {traceback.format_exc()}")
        return None
    finally:
        await client.close()





######################################     HANDLER CONDITION    ######################################


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


######################################     ESCAPE SPECIAL CHARACTERS    ######################################

import html
import traceback



import re
import html


def strip_html_tags(text: str) -> str:
    """
    حذف تمام تگ‌های HTML از متن و بازگرداندن متن ساده
    
    Args:
        text: متن ورودی با تگ‌های HTML
    
    Returns:
        متن ساده بدون تگ
    """
    if not text:
        return ""
    
    # حذف تمام تگ‌های HTML
    clean_text = re.sub(r'<[^>]+>', '', text)
    
    # فرار کردن کاراکترهای خاص
    clean_text = html.escape(clean_text)
    
    return clean_text


def keep_only_text(text: str) -> str:
    """
    نگهداری فقط متن ساده (مناسب برای بله)
    """
    if not text:
        return ""
    
    # حذف تگ‌های HTML
    text = re.sub(r'<[^>]+>', '', text)
    
    # جایگزینی موجودیت‌های HTML
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&amp;', '&')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    
    return text



