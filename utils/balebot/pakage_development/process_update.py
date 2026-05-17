# # utils/balebot/pakage_development/process_update.py

# import logging
# import trace
# import traceback
# import aiohttp
# from balethon import Client
# from typing import Callable, Optional, Dict, Any, Union
# import asyncio

# logger = logging.getLogger(__name__)

# # ================================================
# # تنظیمات ثابت برای دور زدن DNS
# # ================================================
# BOT_API_IP = "2.189.68.126"
# HEADERS = {"Host": "tapi.bale.ai"}

# class MyCustomBot(Client):
#     """کلاس سفارشی ربات با قابلیت پردازش وب‌هوک"""

#     def __init__(self, token, *args, **kwargs):
#         super().__init__(token, *args, **kwargs)
#         self.command_handlers = {}
#         self.message_handlers = []
#         self.custom_token = token
#         self._delete_session = None

#     async def send_message_direct(
#         self, 
#         chat_id: int, 
#         text: str, 
#         parse_mode: str = "Markdown",
#         reply_markup: Any = None
#     ):
#         """ارسال مستقیم پیام با IP و Host Header"""
#         url = f"https://{BOT_API_IP}/bot{self.custom_token}/sendMessage"
#         payload = {
#             "chat_id": chat_id,
#             "text": text,
#             "parse_mode": parse_mode
#         }
        
#         # اضافه کردن reply_markup اگر وجود داشته باشد
#         if reply_markup:
#             payload["reply_markup"] = reply_markup

#         try:
#             connector = aiohttp.TCPConnector()
#             async with aiohttp.ClientSession(connector=connector, headers=HEADERS) as session:
#                 async with session.post(url, json=payload, ssl=False) as response:
#                     if response.status == 200:
#                         try:
#                             result = await response.json()
#                             if result.get('ok'):
#                                 logger.info(f"Message sent to {chat_id}")
#                                 return result
#                         except:
#                             pass
#         except Exception as e:
#             logger.error(f"Send error: {traceback.format_exc()}")
#         return None

#     def on_message(self, condition: Optional[Callable] = None):
#         """دکوریتور برای ثبت هندلرهای پیام با شرط"""
#         def decorator(func: Callable):
#             self.message_handlers.append({
#                 "func": func,
#                 "condition": condition
#             })
#             return func
#         return decorator

#     def on_command(self, command_name: str):
#         """دکوریتور برای ثبت هندلر دستورات"""
#         def decorator(func: Callable):
#             self.command_handlers[command_name] = func
#             return func
#         return decorator

#     def _create_message_object(self, raw_data: Dict[str, Any]):
#         """
#         ایجاد یک شیء کامل از دیتای خام که با بالیتون سازگار باشد
#         """
#         class SimpleUser:
#             def __init__(self, data):
#                 self.id = data.get('id')
#                 self.first_name = data.get('first_name', '')
#                 self.last_name = data.get('last_name', '')
#                 self.username = data.get('username', '')
#                 self.is_bot = data.get('is_bot', False)
#                 self.language_code = data.get('language_code', '')
        
#         class SimpleChat:
#             def __init__(self, data):
#                 self.id = data.get('id')
#                 self.type = data.get('type', 'private')
#                 self.first_name = data.get('first_name', '')
#                 self.last_name = data.get('last_name', '')
#                 self.username = data.get('username', '')
#                 self.title = data.get('title', '')
        
#         class MessageResult:
#             """کلاس نتیجه برای برگرداندن message_id"""
#             __slots__ = ('message_id',)
#             def __init__(self, message_id):
#                 self.message_id = message_id
        
#         class SimpleMessage:
#             __slots__ = ('_raw', '_bot', 'message_id', 'date', 'text', 'author', 'chat')
            
#             def __init__(self, data, bot_instance):
#                 self._raw = data
#                 self._bot = bot_instance
#                 self.message_id = data.get('message_id')
#                 self.date = data.get('date')
#                 self.text = data.get('text', '')
                
#                 from_data = data.get('from', {})
#                 self.author = SimpleUser(from_data)
                
#                 chat_data = data.get('chat', {})
#                 self.chat = SimpleChat(chat_data)
            
#             async def reply(self, text: str, reply_markup=None, **kwargs) -> MessageResult:
#                 """
#                 ارسال پاسخ به پیام و برگرداندن نتیجه با message_id
#                 """
#                 markup_dict = None
#                 if reply_markup:
#                     if hasattr(reply_markup, 'keyboard'):
#                         keyboard_rows = []
#                         for row in reply_markup.keyboard:
#                             button_row = []
#                             for btn in row:
#                                 button_row.append({"text": btn.text})
#                             keyboard_rows.append(button_row)
#                         markup_dict = {
#                             "keyboard": keyboard_rows,
#                             "resize_keyboard": getattr(reply_markup, 'resize_keyboard', True),
#                             "one_time_keyboard": getattr(reply_markup, 'one_time_keyboard', False)
#                         }
#                     elif hasattr(reply_markup, 'inline_keyboard'):
#                         keyboard_rows = []
#                         for row in reply_markup.inline_keyboard:
#                             button_row = []
#                             for btn in row:
#                                 button_row.append({
#                                     "text": btn.text,
#                                     "callback_data": getattr(btn, 'callback_data', None),
#                                     "url": getattr(btn, 'url', None)
#                                 })
#                             keyboard_rows.append(button_row)
#                         markup_dict = {"inline_keyboard": keyboard_rows}
#                     else:
#                         markup_dict = reply_markup
                
#                 # ارسال پیام و دریافت نتیجه
#                 result = await self._bot.send_message_direct(
#                     chat_id=self.chat.id,
#                     text=text,
#                     reply_markup=markup_dict
#                 )
                
#                 # استخراج message_id از نتیجه
#                 message_id = None
#                 if result:
#                     # ساختار پاسخ بالیتون معمولاً به این شکل است
#                     if isinstance(result, dict):
#                         if result.get('result') and isinstance(result['result'], dict):
#                             message_id = result['result'].get('message_id')
#                         elif result.get('message_id'):
#                             message_id = result.get('message_id')
                    
#                     # لاگ برای دیباگ
#                     print(f"Reply result: {result}, extracted message_id: {message_id}")
                
#                 return MessageResult(message_id)
            
#             async def send_message(self, text: str, reply_markup: Any = None, **kwargs) -> MessageResult:
#                 """Alias for reply"""
#                 return await self.reply(text, reply_markup=reply_markup)
        
#         return SimpleMessage(raw_data, self)
    
#     async def process_update(self, update_data: Dict[str, Any]):
#         """پردازش آپدیت‌های دریافتی از بله"""
#         try:
#             if 'message' not in update_data:
#                 return

#             message = self._create_message_object(update_data['message'])
            
#             text = message.text or ""
#             chat_id = message.chat.id

#             # اولویت اول: دستورات
#             if text and text.startswith('/'):
#                 command_name = text.split()[0][1:].split('@')[0]
#                 if command_name in self.command_handlers:
#                     await self.command_handlers[command_name](message)
#                     return

#             # اولویت دوم: هندلرهای عمومی با شرط
#             for handler in self.message_handlers:
#                 condition = handler.get("condition")
#                 if condition is None:
#                     await handler["func"](message)
#                     return
#                 elif callable(condition):
#                     try:
#                         # ✅ روش صحیح تشخیص coroutine
#                         import asyncio
#                         if asyncio.iscoroutinefunction(condition):
#                             # اگر تابع async است
#                             result = await condition(message)
#                         else:
#                             # اگر تابع sync است
#                             result = condition(message)
                        
#                         if result:
#                             await handler["func"](message)
#                             return
#                     except Exception as e:
#                         logger.debug(f"Condition failed: {traceback.format_exc()}")

#         except Exception as e:
#             logger.error(f"Error in process_update: {traceback.format_exc()}", exc_info=True)

    
#     async def _get_delete_session(self):
#         """دریافت session برای درخواست‌های حذف"""
#         if self._delete_session is None or self._delete_session.closed:
#             connector = aiohttp.TCPConnector()
#             self._delete_session = aiohttp.ClientSession(
#                 connector=connector, 
#                 headers=HEADERS
#             )
#         return self._delete_session

#     async def delete_message_safe(self, chat_id: int, message_id: int) -> bool:
#         """
#         حذف ایمن پیام - بدون خطا
        
#         Args:
#             chat_id: شناسه چت
#             message_id: شناسه پیام
        
#         Returns:
#             bool: موفقیت آمیز بودن عملیات
#         """
#         url = f"https://{BOT_API_IP}/bot{self.custom_token}/deleteMessage"
#         payload = {
#             "chat_id": chat_id,
#             "message_id": message_id
#         }
        
#         for attempt in range(2):  # حداکثر 2 بار تلاش
#             try:
#                 session = await self._get_delete_session()
#                 async with session.post(url, json=payload, ssl=False) as response:
#                     if response.status == 200:
#                         result = await response.json()
#                         if result.get('ok'):
#                             logger.info(f"Message {message_id} deleted in chat {chat_id}")
#                             return True
#                     else:
#                         logger.warning(f"Delete failed with status {response.status}")
#             except Exception as e:
#                 logger.error(f"Delete attempt {attempt + 1} failed: {traceback.format_exc()}")
#                 if attempt == 0:
#                     # بستن session و تلاش مجدد
#                     if self._delete_session:
#                         await self._delete_session.close()
#                         self._delete_session = None
#                     await asyncio.sleep(0.5)
        
#         return False

#     async def delete_message(self, chat_id: int, message_id: int):
#         """
#         Override متد delete_message برای استفاده از روش مستقیم
#         """
#         return await self.delete_message_safe(chat_id, message_id)

# # ================================================
# # نمونه سراسری از ربات
# # ================================================
# from utils.variables.TOKEN import BTOKEN as TOKEN
# bot = MyCustomBot(TOKEN)


# utils/balebot/pakage_development/process_update.py

import logging
import traceback
import aiohttp
from balethon import Client
from typing import Callable, Optional, Dict, Any
import asyncio

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
    
    async def reply(self, text: str, reply_markup=None, **kwargs) -> MessageResult:
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
            parse_mode="HTML"
        )
        
        message_id = None
        if result and isinstance(result, dict):
            if result.get('result') and isinstance(result['result'], dict):
                message_id = result['result'].get('message_id')
            elif result.get('message_id'):
                message_id = result.get('message_id')
        
        return MessageResult(message_id)
    
    async def send_message(self, text: str, reply_markup: Any = None, **kwargs) -> MessageResult:
        return await self.reply(text, reply_markup=reply_markup)


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
        }
        
        if parse_mode:
            payload["parse_mode"] = parse_mode
        
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
                            logger.info(f"Message sent to {chat_id}")
                            return result
            except asyncio.TimeoutError:
                logger.error(f"Timeout sending message to {chat_id}")
            except Exception as e:
                logger.error(f"Send error: {traceback.format_exc()}")
        
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

