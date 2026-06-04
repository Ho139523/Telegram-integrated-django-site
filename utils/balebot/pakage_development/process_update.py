# utils/balebot/pakage_development/process_update.py

import logging
import traceback
import aiohttp
from balethon import Client
from typing import Callable, Optional, Dict, Any, List
import asyncio
import json
from utils.telbot.functions import measure_performance

logger = logging.getLogger(__name__)

# ================================================
# تنظیمات ثابت برای دور زدن DNS
# ================================================
BOT_API_IP = "2.189.68.126"
HEADERS = {"Host": "tapi.bale.ai"}


class MessageResult:
    """کلاس نتیجه برای برگرداندن message_id"""
    __slots__ = ('message_id',)
    def __init__(self, message_id: int):
        self.message_id = message_id


class SimpleUser:
    __slots__ = ('id', 'first_name', 'last_name', 'username', 'is_bot', 'language_code')
    def __init__(self, data):
        self.id = data.get('id')
        self.first_name = data.get('first_name', '')
        self.last_name = data.get('last_name', '')
        self.username = data.get('username', '')
        self.is_bot = data.get('is_bot', False)
        self.language_code = data.get('language_code', '')


class SimpleChat:
    __slots__ = ('id', 'type', 'first_name', 'last_name', 'username', 'title')
    def __init__(self, data):
        self.id = data.get('id')
        self.type = data.get('type', 'private')
        self.first_name = data.get('first_name', '')
        self.last_name = data.get('last_name', '')
        self.username = data.get('username', '')
        self.title = data.get('title', '')


class SimpleMessage:
    __slots__ = ('_raw', '_bot', 'message_id', 'date', 'text', 'author', 'chat')
    
    def __init__(self, data, bot_instance):
        self._raw = data
        self._bot = bot_instance
        self.message_id = data.get('message_id')
        self.date = data.get('date')
        self.text = data.get('text', '')
        
        from_data = data.get('from', {})
        self.author = SimpleUser(from_data)
        
        chat_data = data.get('chat', {})
        self.chat = SimpleChat(chat_data)
    
    async def reply(self, text: str, reply_markup=None, parse_mode: str = "HTML", **kwargs) -> MessageResult:
        """ارسال پاسخ به پیام و برگرداندن نتیجه با message_id"""
        markup_dict = None
        if reply_markup:
            if hasattr(reply_markup, 'generate_keyboard'):
                reply_markup = reply_markup.generate_keyboard()
            
            if hasattr(reply_markup, 'inline_keyboard'):
                keyboard_rows = []
                for row in reply_markup.inline_keyboard:
                    button_row = []
                    for btn in row:
                        button_data = {"text": btn.text}
                        if hasattr(btn, 'callback_data') and btn.callback_data:
                            button_data["callback_data"] = btn.callback_data
                        if hasattr(btn, 'url') and btn.url:
                            button_data["url"] = btn.url
                        button_row.append(button_data)
                    keyboard_rows.append(button_row)
                markup_dict = {"inline_keyboard": keyboard_rows}
            elif hasattr(reply_markup, 'keyboard'):
                keyboard_rows = []
                for row in reply_markup.keyboard:
                    button_row = []
                    for btn in row:
                        button_row.append({"text": btn.text})
                    keyboard_rows.append(button_row)
                markup_dict = {
                    "keyboard": keyboard_rows,
                    "resize_keyboard": getattr(reply_markup, 'resize_keyboard', True),
                    "one_time_keyboard": getattr(reply_markup, 'one_time_keyboard', False)
                }
            else:
                markup_dict = reply_markup
        
        result = await self._bot.send_message_direct(
            chat_id=self.chat.id,
            text=text,
            reply_markup=markup_dict,
            parse_mode=parse_mode
        )
        
        message_id = None
        if result and isinstance(result, dict):
            if result.get('result') and isinstance(result['result'], dict):
                message_id = result['result'].get('message_id')
            elif result.get('message_id'):
                message_id = result.get('message_id')
        
        return MessageResult(message_id)

    async def send_message(self, text: str, reply_markup: Any = None, parse_mode: str = "HTML", **kwargs) -> MessageResult:
        return await self.reply(text, reply_markup, parse_mode=parse_mode)


class SimpleCallbackQuery:
    """کلاس ساده برای پردازش CallbackQuery"""
    __slots__ = ('_raw', '_bot', 'id', 'from_user', 'message', 'data')
    
    def __init__(self, data, bot_instance):
        self._raw = data
        self._bot = bot_instance
        self.id = data.get('id')
        self.data = data.get('data', '')
        
        from_data = data.get('from', {})
        self.from_user = SimpleUser(from_data) if from_data else None
        
        message_data = data.get('message', {})
        if message_data:
            self.message = SimpleMessage(message_data, bot_instance)
        else:
            self.message = None
    
    async def answer(self, text: str = None, show_alert: bool = False, **kwargs) -> bool:
        """پاسخ به callback"""
        url = f"https://{BOT_API_IP}/bot{self._bot.custom_token}/answerCallbackQuery"
        payload = {
            "callback_query_id": self.id,
            "text": text or "",
            "show_alert": show_alert
        }
        
        connector = aiohttp.TCPConnector(force_close=True)
        async with aiohttp.ClientSession(connector=connector, headers=HEADERS) as session:
            try:
                async with session.post(url, json=payload, ssl=False, timeout=10) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('ok', False)
            except Exception as e:
                logger.error(f"Error answering callback: {e}")
        return False


class MyCustomBot(Client):
    """کلاس سفارشی ربات با قابلیت پردازش وب‌هوک"""

    def __init__(self, token, *args, **kwargs):
        super().__init__(token, *args, **kwargs)
        self.command_handlers = {}
        self.message_handlers = []
        self.callback_handlers = []
        self.custom_token = token

    # ================================================
    # ارسال مستقیم پیام
    # ================================================

    async def send_message_direct(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = "HTML",
        reply_markup: Any = None
    ):
        """ارسال مستقیم پیام با IP و Host Header"""
        url = f"https://{BOT_API_IP}/bot{self.custom_token}/sendMessage"
        
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        
        if not parse_mode:
            payload.pop("parse_mode", None)
        
        if reply_markup:
            if hasattr(reply_markup, 'generate_keyboard'):
                reply_markup = reply_markup.generate_keyboard()
            
            if hasattr(reply_markup, 'to_dict'):
                payload["reply_markup"] = reply_markup.to_dict()
            elif hasattr(reply_markup, 'inline_keyboard'):
                keyboard_rows = []
                for row in reply_markup.inline_keyboard:
                    button_row = []
                    for btn in row:
                        button_data = {"text": btn.text}
                        if hasattr(btn, 'callback_data') and btn.callback_data:
                            button_data["callback_data"] = btn.callback_data
                        if hasattr(btn, 'url') and btn.url:
                            button_data["url"] = btn.url
                        button_row.append(button_data)
                    keyboard_rows.append(button_row)
                payload["reply_markup"] = {"inline_keyboard": keyboard_rows}
            elif hasattr(reply_markup, 'keyboard'):
                keyboard_rows = []
                for row in reply_markup.keyboard:
                    button_row = []
                    for btn in row:
                        button_row.append({"text": btn.text})
                    keyboard_rows.append(button_row)
                payload["reply_markup"] = {
                    "keyboard": keyboard_rows,
                    "resize_keyboard": getattr(reply_markup, 'resize_keyboard', True),
                    "one_time_keyboard": getattr(reply_markup, 'one_time_keyboard', False)
                }
            else:
                payload["reply_markup"] = reply_markup
        
        connector = aiohttp.TCPConnector(force_close=True)
        async with aiohttp.ClientSession(connector=connector, headers=HEADERS) as session:
            try:
                async with session.post(url, json=payload, ssl=False, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            logger.info(f"Message sent to {chat_id} with parse_mode={parse_mode}")
                            return result
            except asyncio.TimeoutError:
                logger.error(f"Timeout sending message to {chat_id}")
            except Exception as e:
                logger.error(f"Send error: {traceback.format_exc()}")
        
        return None

    # ================================================
    # ارسال گروه رسانه‌ای (آلبوم عکس)
    # ================================================

    async def send_media_group(
    self,
    chat_id: int,
    media: List[Dict[str, Any]],
    reply_to_message_id: int = None
):
        """
        ارسال گروه رسانه‌ای با فرمت صحیح multipart/form-data
        """
        import json
        import time
    
        url = f"https://{BOT_API_IP}/bot{self.custom_token}/sendMediaGroup"
    
        # آماده‌سازی media: فقط caption برای اولین عکس
        clean_media = []
        for i, item in enumerate(media):
            m = dict(item)
            if i > 0:
                m.pop("caption", None)
                m.pop("parse_mode", None)
            clean_media.append(m)
    
        # ساخت payload
        payload = {
            "chat_id": str(chat_id),
            "media": json.dumps(clean_media)  # تبدیل لیست به رشته JSON
        }
    
        if reply_to_message_id:
            payload["reply_to_message_id"] = str(reply_to_message_id)
    
        # دیباگ
        print(f"📤 Sending media group with {len(clean_media)} images")
        print(f"   First image URL: {clean_media[0].get('media', 'N/A')[:80]}...")
    
        # اندازه‌گیری زمان
        start_time = time.perf_counter()
        
        connector = aiohttp.TCPConnector(force_close=True)
        async with aiohttp.ClientSession(connector=connector, headers=HEADERS) as session:
            try:
                async with session.post(url, data=payload, ssl=False, timeout=60) as response:
                    response_text = await response.text()
                    
                    # محاسبه زمان elapsed به صورت دستی
                    elapsed_ms = (time.perf_counter() - start_time) * 1000
    
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            print("✅ Media group sent successfully")
                            return result.get('result', [])

                        else:
                            logger.error(f"API error: {result}")
                    else:
                        logger.error(f"HTTP {response.status}: {response_text[:200]}")
                        
                    print(f"⏱ زمان پاسخ: {elapsed_ms:.0f}ms")
    
            except asyncio.TimeoutError:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                logger.error(f"Timeout after {elapsed_ms:.0f}ms sending media group to {chat_id}")
            except Exception as e:
                logger.error(f"Send media group error: {traceback.format_exc()}")
        
        return None
    
    # ================================================
    # حذف پیام
    # ================================================

    async def delete_message(self, chat_id: int, message_id: int) -> bool:
        """حذف پیام با استفاده از API مستقیم"""
        if not message_id:
            return False
        
        url = f"https://{BOT_API_IP}/bot{self.custom_token}/deleteMessage"
        payload = {
            "chat_id": chat_id,
            "message_id": message_id
        }
        
        connector = aiohttp.TCPConnector(force_close=True)
        async with aiohttp.ClientSession(connector=connector, headers=HEADERS) as session:
            try:
                async with session.post(url, json=payload, ssl=False, timeout=10) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            logger.info(f"Message {message_id} deleted")
                            return True
            except asyncio.TimeoutError:
                logger.error(f"Timeout deleting message {message_id}")
            except Exception as e:
                logger.error(f"Delete error: {e}")
        
        return False

    # ================================================
    # دکوریتورهای ثبت هندلر
    # ================================================

    def on_message(self, condition: Optional[Callable] = None):
        def decorator(func: Callable):
            self.message_handlers.append({
                "func": func,
                "condition": condition
            })
            return func
        return decorator

    def on_command(self, command_name: str):
        def decorator(func: Callable):
            self.command_handlers[command_name] = func
            return func
        return decorator

    def on_callback_query(self, condition: Optional[Callable] = None):
        def decorator(func: Callable):
            self.callback_handlers.append({
                "func": func,
                "condition": condition
            })
            return func
        return decorator

    # ================================================
    # ایجاد شیء پیام
    # ================================================

    def _create_message_object(self, raw_data: Dict[str, Any]):
        return SimpleMessage(raw_data, self)

    # ================================================
    # پردازش آپدیت
    # ================================================

    async def process_update(self, update_data: Dict[str, Any]):
        """پردازش آپدیت‌های دریافتی از بله"""
        try:
            # پردازش پیام
            if 'message' in update_data:
                message = self._create_message_object(update_data['message'])
                text = message.text or ""

                if text and text.startswith('/'):
                    command_name = text.split()[0][1:].split('@')[0]
                    if command_name in self.command_handlers:
                        await self.command_handlers[command_name](message)
                        return

                for handler in self.message_handlers:
                    condition = handler.get("condition")
                    if condition is None:
                        await handler["func"](message)
                        return
                    elif callable(condition):
                        try:
                            if asyncio.iscoroutinefunction(condition):
                                result = await condition(message)
                            else:
                                result = condition(message)
                            
                            if result:
                                await handler["func"](message)
                                return
                        except Exception as e:
                            logger.debug(f"Condition failed: {e}")

            # پردازش Callback Query
            elif 'callback_query' in update_data:
                callback = SimpleCallbackQuery(update_data['callback_query'], self)
                
                for handler in self.callback_handlers:
                    condition = handler.get("condition")
                    if condition is None:
                        await handler["func"](callback)
                        return
                    elif callable(condition):
                        try:
                            if asyncio.iscoroutinefunction(condition):
                                result = await condition(callback)
                            else:
                                result = condition(callback)
                            
                            if result:
                                await handler["func"](callback)
                                return
                        except Exception as e:
                            logger.debug(f"Callback condition failed: {e}")

        except Exception as e:
            logger.error(f"Error in process_update: {traceback.format_exc()}")


# ================================================
# نمونه سراسری از ربات
# ================================================
from utils.variables.TOKEN import BTOKEN as TOKEN
bot = MyCustomBot(TOKEN)
