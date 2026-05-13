# # utils/balebot/pakage_development/process_update.py
# BOT_API_IP = "2.189.68.126"
# HEADERS = {"Host": "tapi.bale.ai"}

# import logging
# import aiohttp
# from balethon import Client
# from typing import Callable, Optional, Dict, Any, Union

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
#             logger.error(f"Send error: {e}")
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
        
#         class SimpleMessage:
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
            

#             async def reply(self, text: str, reply_markup=None, **kwargs):
#                 """
#                 ارسال پاسخ به پیام - کاملاً سازگار با API بله
#                 """
#                 # تبدیل reply_markup بالیتون به دیکشنری ساده
#                 markup_dict = None
#                 if reply_markup:
#                     if hasattr(reply_markup, 'keyboard'):
#                         # تبدیل آبجکت ReplyKeyboard بالیتون
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
#                     else:
#                         markup_dict = reply_markup
                
#                 return await self._bot.send_message_direct(
#                     chat_id=self.chat.id,
#                     text=text,
#                     reply_markup=markup_dict
#                 )
            
#             async def send_message(self, text: str, reply_markup: Any = None, **kwargs):
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
#                 command_name = text.split()[0][1:]
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
#                         if hasattr(condition, '__await__'):
#                             result = await condition(message)
#                         else:
#                             result = condition(message)
                        
#                         if result:
#                             await handler["func"](message)
#                             return
#                     except Exception as e:
#                         logger.debug(f"Condition failed: {e}")

#         except Exception as e:
#             logger.error(f"Error in process_update: {e}", exc_info=True)





# utils/balebot/pakage_development/process_update.py
# import logging
# import aiohttp
# from balethon import Client
# from typing import Callable, Optional, Dict, Any, Union
# from utils.variables.TOKEN import BTOKEN as TOKEN
# import asyncio
# import traceback
# from functools import wraps

# logger = logging.getLogger(__name__)

# BOT_API_IP = "2.189.68.126"
# HEADERS = {"Host": "tapi.bale.ai"}


# class SimpleUser:
#     __slots__ = ('id', 'first_name', 'last_name', 'username', 'is_bot', 'language_code')
#     def __init__(self, data):
#         self.id = data.get('id')
#         self.first_name = data.get('first_name', '')
#         self.last_name = data.get('last_name', '')
#         self.username = data.get('username', '')
#         self.is_bot = data.get('is_bot', False)
#         self.language_code = data.get('language_code', '')


# class SimpleChat:
#     __slots__ = ('id', 'type', 'first_name', 'last_name', 'username', 'title')
#     def __init__(self, data):
#         self.id = data.get('id')
#         self.type = data.get('type', 'private')
#         self.first_name = data.get('first_name', '')
#         self.last_name = data.get('last_name', '')
#         self.username = data.get('username', '')
#         self.title = data.get('title', '')


# class SimpleMessage:
#     __slots__ = ('_raw', '_bot', 'message_id', 'date', 'text', 'author', 'from_user', 'chat')
    
#     def __init__(self, data, bot_instance):
#         self._raw = data
#         self._bot = bot_instance
#         self.message_id = data.get('message_id')
#         self.date = data.get('date')
#         self.text = data.get('text', '')
        
#         from_data = data.get('from', {})
#         self.author = SimpleUser(from_data)
#         self.from_user = self.author
        
#         chat_data = data.get('chat', {})
#         self.chat = SimpleChat(chat_data)
    
#     async def reply(self, text: str, reply_markup=None, **kwargs):
#         return await self._bot.send_message_direct(
#             chat_id=self.chat.id,
#             text=text,
#             reply_markup=reply_markup
#         )
    
#     async def send_message(self, text: str, reply_markup: Any = None, **kwargs):
#         return await self.reply(text, reply_markup=reply_markup)


# class MyCustomBot(Client):
#     """کلاس سفارشی ربات با قابلیت پردازش وب‌هوک - بهینه برای ترافیک بالا"""
    
#     def __init__(self, token, *args, **kwargs):
#         super().__init__(token, *args, **kwargs)
#         self.command_handlers = {}
#         self.message_handlers = []
#         self.custom_token = token
#         self._session = None
#         self._connector = None
#         self._session_lock = asyncio.Lock()
#         self._loop = None
        
#     def _get_or_create_event_loop(self):
#         """دریافت یا ایجاد event loop مناسب"""
#         try:
#             loop = asyncio.get_running_loop()
#         except RuntimeError:
#             loop = asyncio.new_event_loop()
#             asyncio.set_event_loop(loop)
#         return loop
        
#     async def _get_session(self):
#         """دریافت یا ایجاد session مشترک با قفل برای جلوگیری از race condition"""
#         if self._session is None or self._session.closed:
#             async with self._session_lock:
#                 if self._session is None or self._session.closed:
#                     timeout = aiohttp.ClientTimeout(total=30, connect=10)
#                     self._connector = aiohttp.TCPConnector(
#                         limit=100,
#                         limit_per_host=50,
#                         ttl_dns_cache=300,
#                         enable_cleanup_closed=True,
#                         force_close=False
#                     )
#                     self._session = aiohttp.ClientSession(
#                         connector=self._connector,
#                         headers=HEADERS,
#                         timeout=timeout
#                     )
#         return self._session
    
#     async def close(self):
#         """بستن graceful session هنگام خاموش شدن"""
#         if self._session and not self._session.closed:
#             await self._session.close()
#         if self._connector and not self._connector.closed:
#             await self._connector.close()

#     async def send_message_direct(
#         self, 
#         chat_id: int, 
#         text: str, 
#         parse_mode: str = "Markdown",
#         reply_markup: Any = None
#     ):
#         """ارسال مستقیم پیام با IP و Host Header - با مدیریت event loop"""
#         url = f"https://{BOT_API_IP}/bot{self.custom_token}/sendMessage"
#         payload = {
#             "chat_id": chat_id,
#             "text": text,
#             "parse_mode": parse_mode
#         }
        
#         if reply_markup:
#             if hasattr(reply_markup, 'keyboard'):
#                 keyboard_rows = []
#                 for row in reply_markup.keyboard:
#                     button_row = []
#                     for btn in row:
#                         button_row.append({"text": btn.text})
#                     keyboard_rows.append(button_row)
#                 payload["reply_markup"] = {
#                     "keyboard": keyboard_rows,
#                     "resize_keyboard": getattr(reply_markup, 'resize_keyboard', True),
#                     "one_time_keyboard": getattr(reply_markup, 'one_time_keyboard', False)
#                 }
#             elif hasattr(reply_markup, 'inline_keyboard'):
#                 keyboard_rows = []
#                 for row in reply_markup.inline_keyboard:
#                     button_row = []
#                     for btn in row:
#                         button_row.append({
#                             "text": btn.text,
#                             "callback_data": getattr(btn, 'callback_data', None),
#                             "url": getattr(btn, 'url', None)
#                         })
#                     keyboard_rows.append(button_row)
#                 payload["reply_markup"] = {"inline_keyboard": keyboard_rows}
#             else:
#                 payload["reply_markup"] = reply_markup

#         # حداکثر 3 بار تلاش مجدد
#         for attempt in range(3):
#             try:
#                 session = await self._get_session()
#                 async with session.post(url, json=payload, ssl=False) as response:
#                     if response.status == 200:
#                         result = await response.json()
#                         if result.get('ok'):
#                             return result
#                     else:
#                         logger.warning(f"Send failed with status {response.status}")
#             except RuntimeError as e:
#                 if "Event loop is closed" in str(e):
#                     # ایجاد session جدید در صورت بسته شدن event loop
#                     logger.warning(f"Event loop closed, recreating session (attempt {attempt + 1})")
#                     self._session = None
#                     self._connector = None
#                     await asyncio.sleep(0.1)
#                     continue
#                 logger.error(f"Runtime error: {e}")
#             except aiohttp.ClientError as e:
#                 logger.error(f"Client error: {e}")
#             except asyncio.TimeoutError:
#                 logger.error(f"Timeout sending message to {chat_id}")
#             except Exception as e:
#                 logger.error(f"Send error: {traceback.format_exc()}")
            
#             if attempt < 2:
#                 await asyncio.sleep(0.1 * (attempt + 1))
        
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
#         """ایجاد یک شیء پیام از دیتای خام"""
#         return SimpleMessage(raw_data, self)

#     async def process_update(self, update_data: Dict[str, Any]):
#         """پردازش آپدیت‌های دریافتی از بله - بهینه شده"""
#         try:
#             if 'message' not in update_data:
#                 return

#             message = self._create_message_object(update_data['message'])
#             text = message.text or ""

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
#                         if asyncio.iscoroutinefunction(condition):
#                             result = await condition(message)
#                         else:
#                             result = condition(message)
                        
#                         if result:
#                             await handler["func"](message)
#                             return
#                     except Exception as e:
#                         logger.debug(f"Condition failed: {e}")

#         except Exception as e:
#             logger.error(f"Error in process_update: {e}", exc_info=True)


# # utils/balebot/pakage_development/process_update.py
# import logging
# import aiohttp
# from balethon import Client
# from typing import Callable, Optional, Dict, Any, Union
# from utils.variables.TOKEN import BTOKEN as TOKEN
# import asyncio
# import traceback
# from functools import wraps

# logger = logging.getLogger(__name__)

# BOT_API_IP = "2.189.68.126"
# HEADERS = {"Host": "tapi.bale.ai"}


# class SimpleUser:
#     __slots__ = ('id', 'first_name', 'last_name', 'username', 'is_bot', 'language_code')
#     def __init__(self, data):
#         self.id = data.get('id')
#         self.first_name = data.get('first_name', '')
#         self.last_name = data.get('last_name', '')
#         self.username = data.get('username', '')
#         self.is_bot = data.get('is_bot', False)
#         self.language_code = data.get('language_code', '')


# class SimpleChat:
#     __slots__ = ('id', 'type', 'first_name', 'last_name', 'username', 'title')
#     def __init__(self, data):
#         self.id = data.get('id')
#         self.type = data.get('type', 'private')
#         self.first_name = data.get('first_name', '')
#         self.last_name = data.get('last_name', '')
#         self.username = data.get('username', '')
#         self.title = data.get('title', '')


# class SimpleMessage:
#     __slots__ = ('_raw', '_bot', 'message_id', 'date', 'text', 'author', 'from_user', 'chat')
    
#     def __init__(self, data, bot_instance):
#         self._raw = data
#         self._bot = bot_instance
#         self.message_id = data.get('message_id')
#         self.date = data.get('date')
#         self.text = data.get('text', '')
        
#         from_data = data.get('from', {})
#         self.author = SimpleUser(from_data)
#         self.from_user = self.author
        
#         chat_data = data.get('chat', {})
#         self.chat = SimpleChat(chat_data)
    
#     async def reply(self, text: str, reply_markup=None, **kwargs):
#         return await self._bot.send_message_direct(
#             chat_id=self.chat.id,
#             text=text,
#             reply_markup=reply_markup
#         )
    
#     async def send_message(self, text: str, reply_markup: Any = None, **kwargs):
#         return await self.reply(text, reply_markup=reply_markup)


# class MyCustomBot(Client):
#     """کلاس سفارشی ربات با قابلیت پردازش وب‌هوک - بهینه برای ترافیک بالا"""
    
#     def __init__(self, token, *args, **kwargs):
#         super().__init__(token, *args, **kwargs)
#         self.command_handlers = {}
#         self.message_handlers = []
#         self.custom_token = token
#         self._session = None
#         self._connector = None
#         self._session_lock = asyncio.Lock()
#         self._loop = None
        
#     def _get_or_create_event_loop(self):
#         """دریافت یا ایجاد event loop مناسب"""
#         try:
#             loop = asyncio.get_running_loop()
#         except RuntimeError:
#             loop = asyncio.new_event_loop()
#             asyncio.set_event_loop(loop)
#         return loop
        
#     async def _get_session(self):
#         """دریافت یا ایجاد session مشترک با قفل برای جلوگیری از race condition"""
#         if self._session is None or self._session.closed:
#             async with self._session_lock:
#                 if self._session is None or self._session.closed:
#                     timeout = aiohttp.ClientTimeout(total=30, connect=10)
#                     self._connector = aiohttp.TCPConnector(
#                         limit=100,
#                         limit_per_host=50,
#                         ttl_dns_cache=300,
#                         enable_cleanup_closed=True,
#                         force_close=False
#                     )
#                     self._session = aiohttp.ClientSession(
#                         connector=self._connector,
#                         headers=HEADERS,
#                         timeout=timeout
#                     )
#         return self._session
    
#     async def close(self):
#         """بستن graceful session هنگام خاموش شدن"""
#         if self._session and not self._session.closed:
#             await self._session.close()
#         if self._connector and not self._connector.closed:
#             await self._connector.close()

#     async def send_message_direct(
#         self, 
#         chat_id: int, 
#         text: str, 
#         parse_mode: str = "Markdown",
#         reply_markup: Any = None
#     ):
#         """ارسال مستقیم پیام با IP و Host Header - با مدیریت event loop"""
#         url = f"https://{BOT_API_IP}/bot{self.custom_token}/sendMessage"
#         payload = {
#             "chat_id": chat_id,
#             "text": text,
#             "parse_mode": parse_mode
#         }
        
#         if reply_markup:
#             if hasattr(reply_markup, 'keyboard'):
#                 keyboard_rows = []
#                 for row in reply_markup.keyboard:
#                     button_row = []
#                     for btn in row:
#                         button_row.append({"text": btn.text})
#                     keyboard_rows.append(button_row)
#                 payload["reply_markup"] = {
#                     "keyboard": keyboard_rows,
#                     "resize_keyboard": getattr(reply_markup, 'resize_keyboard', True),
#                     "one_time_keyboard": getattr(reply_markup, 'one_time_keyboard', False)
#                 }
#             elif hasattr(reply_markup, 'inline_keyboard'):
#                 keyboard_rows = []
#                 for row in reply_markup.inline_keyboard:
#                     button_row = []
#                     for btn in row:
#                         button_row.append({
#                             "text": btn.text,
#                             "callback_data": getattr(btn, 'callback_data', None),
#                             "url": getattr(btn, 'url', None)
#                         })
#                     keyboard_rows.append(button_row)
#                 payload["reply_markup"] = {"inline_keyboard": keyboard_rows}
#             else:
#                 payload["reply_markup"] = reply_markup

#         # حداکثر 3 بار تلاش مجدد
#         for attempt in range(3):
#             try:
#                 session = await self._get_session()
#                 async with session.post(url, json=payload, ssl=False) as response:
#                     if response.status == 200:
#                         result = await response.json()
#                         if result.get('ok'):
#                             return result
#                     else:
#                         logger.warning(f"Send failed with status {response.status}")
#             except RuntimeError as e:
#                 if "Event loop is closed" in str(e):
#                     # ایجاد session جدید در صورت بسته شدن event loop
#                     logger.warning(f"Event loop closed, recreating session (attempt {attempt + 1})")
#                     self._session = None
#                     self._connector = None
#                     await asyncio.sleep(0.1)
#                     continue
#                 logger.error(f"Runtime error: {e}")
#             except aiohttp.ClientError as e:
#                 logger.error(f"Client error: {e}")
#             except asyncio.TimeoutError:
#                 logger.error(f"Timeout sending message to {chat_id}")
#             except Exception as e:
#                 logger.error(f"Send error: {traceback.format_exc()}")
            
#             if attempt < 2:
#                 await asyncio.sleep(0.1 * (attempt + 1))
        
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
#         """ایجاد یک شیء پیام از دیتای خام"""
#         return SimpleMessage(raw_data, self)

#     async def process_update(self, update_data: Dict[str, Any]):
#         """پردازش آپدیت‌های دریافتی از بله - بهینه شده"""
#         try:
#             if 'message' not in update_data:
#                 return

#             message = self._create_message_object(update_data['message'])
#             text = message.text or ""

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
#                         if asyncio.iscoroutinefunction(condition):
#                             result = await condition(message)
#                         else:
#                             result = condition(message)
                        
#                         if result:
#                             await handler["func"](message)
#                             return
#                     except Exception as e:
#                         logger.debug(f"Condition failed: {e}")

#         except Exception as e:
#             logger.error(f"Error in process_update: {e}", exc_info=True)


# # ایجاد نمونه سراسری از ربات
# bot = MyCustomBot(TOKEN)

# utils/balebot/pakage_development/process_update.py
# import logging
# import aiohttp
# from balethon import Client
# from balethon.objects import Message, CallbackQuery, User, Chat
# from typing import Callable, Optional, Dict, Any, Union
# from utils.variables.TOKEN import BTOKEN as TOKEN
# import asyncio
# import traceback

# logger = logging.getLogger(__name__)

# BOT_API_IP = "2.189.68.126"
# HEADERS = {"Host": "tapi.bale.ai"}


# # ================================================
# # کلاس‌های ساده (کارآمد برای حافظه)
# # ================================================

# class SimpleUser:
#     __slots__ = ('id', 'first_name', 'last_name', 'username', 'is_bot', 'language_code')
#     def __init__(self, data):
#         self.id = data.get('id')
#         self.first_name = data.get('first_name', '')
#         self.last_name = data.get('last_name', '')
#         self.username = data.get('username', '')
#         self.is_bot = data.get('is_bot', False)
#         self.language_code = data.get('language_code', '')


# class SimpleChat:
#     __slots__ = ('id', 'type', 'first_name', 'last_name', 'username', 'title')
#     def __init__(self, data):
#         self.id = data.get('id')
#         self.type = data.get('type', 'private')
#         self.first_name = data.get('first_name', '')
#         self.last_name = data.get('last_name', '')
#         self.username = data.get('username', '')
#         self.title = data.get('title', '')


# # ================================================
# # کلاس Message Proxy که از Message بالیتون ارث‌بری می‌کند
# # ================================================

# class SimpleMessage(Message):
#     """
#     کلاس پیام سفارشی که هم از Message بالیتون ارث‌بری می‌کند
#     و هم با دیتای خام بله کار می‌کند
#     """
#     __slots__ = ('_raw', '_bot', '_simple_user', '_simple_chat')
    
#     def __init__(self, data, bot_instance):
#         # ذخیره دیتای خام
#         self._raw = data
#         self._bot = bot_instance
        
#         # ساخت اشیاء ساده برای دسترسی سریع
#         from_data = data.get('from', {})
#         self._simple_user = SimpleUser(from_data)
        
#         chat_data = data.get('chat', {})
#         self._simple_chat = SimpleChat(chat_data)
        
#         # فراخوانی سازنده Message بالیتون
#         super().__init__(
#             message_id=data.get('message_id'),
#             date=data.get('date'),
#             text=data.get('text', ''),
#             chat=self._simple_chat,  # اینجا chat ما که از Chat بالیتون ارث‌بری نمی‌کند
#             from_user=self._simple_user,
#             bot=bot_instance,
#             raw=data
#         )
    
#     # دسترسی به properties
#     @property
#     def chat(self):
#         return self._simple_chat
    
#     @property
#     def from_user(self):
#         return self._simple_user
    
#     @property
#     def author(self):
#         return self._simple_user
    
#     async def reply(self, text: str, reply_markup=None, **kwargs):
#         return await self._bot.send_message_direct(
#             chat_id=self.chat.id,
#             text=text,
#             reply_markup=reply_markup
#         )
    
#     async def send_message(self, text: str, reply_markup: Any = None, **kwargs):
#         return await self.reply(text, reply_markup=reply_markup)


# # ================================================
# # کلاس CallbackQuery Proxy
# # ================================================

# class SimpleCallbackQuery(CallbackQuery):
#     """کلاس callback_query سفارشی که از CallbackQuery بالیتون ارث‌بری می‌کند"""
#     __slots__ = ('_raw', '_bot', '_simple_from', '_simple_message')
    
#     def __init__(self, data, bot_instance):
#         self._raw = data
#         self._bot = bot_instance
        
#         from_data = data.get('from', {})
#         self._simple_from = SimpleUser(from_data)
        
#         message_data = data.get('message', {})
#         self._simple_message = SimpleMessage(message_data, bot_instance) if message_data else None
        
#         super().__init__(
#             id=data.get('id'),
#             from_user=self._simple_from,
#             message=self._simple_message,
#             data=data.get('data', ''),
#             bot=bot_instance,
#             raw=data
#         )
    
#     async def answer(self, text: str = None, show_alert: bool = False, **kwargs):
#         if hasattr(self._bot, 'answer_callback_direct'):
#             return await self._bot.answer_callback_direct(
#                 callback_query_id=self.id,
#                 text=text,
#                 show_alert=show_alert
#             )
#         return await super().answer(text, show_alert=show_alert)


# # ================================================
# # کلاس اصلی ربات
# # ================================================

# class MyCustomBot(Client):
#     """کلاس سفارشی ربات با قابلیت پردازش وب‌هوک"""
    
#     def __init__(self, token, *args, **kwargs):
#         super().__init__(token, *args, **kwargs)
#         self.command_handlers = {}
#         self.message_handlers = []
#         self.callback_handlers = []
#         self.custom_token = token
#         self._session = None
#         self._connector = None
#         self._session_lock = asyncio.Lock()
        
#     async def _get_session(self):
#         if self._session is None or self._session.closed:
#             async with self._session_lock:
#                 if self._session is None or self._session.closed:
#                     timeout = aiohttp.ClientTimeout(total=30, connect=10)
#                     self._connector = aiohttp.TCPConnector(
#                         limit=100,
#                         limit_per_host=50,
#                         ttl_dns_cache=300,
#                         enable_cleanup_closed=True
#                     )
#                     self._session = aiohttp.ClientSession(
#                         connector=self._connector,
#                         headers=HEADERS,
#                         timeout=timeout
#                     )
#         return self._session
    
#     async def close(self):
#         if self._session and not self._session.closed:
#             await self._session.close()
#         if self._connector and not self._connector.closed:
#             await self._connector.close()

#     async def send_message_direct(
#         self, 
#         chat_id: int, 
#         text: str, 
#         parse_mode: str = "Markdown",
#         reply_markup: Any = None
#     ):
#         url = f"https://{BOT_API_IP}/bot{self.custom_token}/sendMessage"
#         payload = {
#             "chat_id": chat_id,
#             "text": text,
#             "parse_mode": parse_mode
#         }
        
#         if reply_markup:
#             if hasattr(reply_markup, 'to_dict'):
#                 payload["reply_markup"] = reply_markup.to_dict()
#             elif hasattr(reply_markup, 'keyboard'):
#                 keyboard_rows = []
#                 for row in reply_markup.keyboard:
#                     button_row = []
#                     for btn in row:
#                         button_row.append({"text": btn.text})
#                     keyboard_rows.append(button_row)
#                 payload["reply_markup"] = {
#                     "keyboard": keyboard_rows,
#                     "resize_keyboard": getattr(reply_markup, 'resize_keyboard', True),
#                     "one_time_keyboard": getattr(reply_markup, 'one_time_keyboard', False)
#                 }
#             elif hasattr(reply_markup, 'inline_keyboard'):
#                 keyboard_rows = []
#                 for row in reply_markup.inline_keyboard:
#                     button_row = []
#                     for btn in row:
#                         button_row.append({
#                             "text": btn.text,
#                             "callback_data": getattr(btn, 'callback_data', None),
#                             "url": getattr(btn, 'url', None)
#                         })
#                     keyboard_rows.append(button_row)
#                 payload["reply_markup"] = {"inline_keyboard": keyboard_rows}
#             else:
#                 payload["reply_markup"] = reply_markup

#         for attempt in range(3):
#             try:
#                 session = await self._get_session()
#                 async with session.post(url, json=payload, ssl=False) as response:
#                     if response.status == 200:
#                         result = await response.json()
#                         if result.get('ok'):
#                             return result
#             except Exception as e:
#                 if attempt < 2:
#                     await asyncio.sleep(0.1 * (attempt + 1))
#                     continue
#                 logger.error(f"Send error: {e}")
#         return None

#     def on_message(self, condition: Optional[Callable] = None):
#         def decorator(func: Callable):
#             self.message_handlers.append({"func": func, "condition": condition})
#             return func
#         return decorator

#     def on_command(self, command_name: str):
#         def decorator(func: Callable):
#             self.command_handlers[command_name] = func
#             return func
#         return decorator
    
#     def on_callback_query(self, condition: Optional[Callable] = None):
#         def decorator(func: Callable):
#             self.callback_handlers.append({"func": func, "condition": condition})
#             return func
#         return decorator

#     async def process_update(self, update_data: Dict[str, Any]):
#         """پردازش آپدیت - برگرداندن اشیاء ارث‌برده از Message و CallbackQuery"""
#         try:
#             # پیام
#             if 'message' in update_data:
#                 # ✅ اینجا message از نوع SimpleMessage است که از Message ارث‌بری می‌کند
#                 message = SimpleMessage(update_data['message'], bot=self)
#                 text = message.text or ""
                
#                 # دستورات
#                 if text and text.startswith('/'):
#                     command_name = text.split()[0][1:].split('@')[0]
#                     if command_name in self.command_handlers:
#                         await self.command_handlers[command_name](message)
#                         return
                
#                 # هندلرهای عمومی
#                 for handler in self.message_handlers:
#                     condition = handler.get("condition")
#                     if condition is None:
#                         await handler["func"](message)
#                         return
#                     elif callable(condition):
#                         try:
#                             if asyncio.iscoroutinefunction(condition):
#                                 result = await condition(message)
#                             else:
#                                 result = condition(message)
#                             if result:
#                                 await handler["func"](message)
#                                 return
#                         except Exception as e:
#                             logger.debug(f"Condition failed: {e}")
            
#             # callback_query
#             elif 'callback_query' in update_data:
#                 callback = SimpleCallbackQuery(update_data['callback_query'], bot=self)
                
#                 for handler in self.callback_handlers:
#                     condition = handler.get("condition")
#                     if condition is None:
#                         await handler["func"](callback)
#                         return
#                     elif callable(condition):
#                         try:
#                             if asyncio.iscoroutinefunction(condition):
#                                 result = await condition(callback)
#                             else:
#                                 result = condition(callback)
#                             if result:
#                                 await handler["func"](callback)
#                                 return
#                         except Exception as e:
#                             logger.debug(f"Callback condition failed: {e}")
                            
#         except Exception as e:
#             logger.error(f"Error in process_update: {traceback.format_exc()}", exc_info=True)


# # ایجاد نمونه سراسری
# bot = MyCustomBot(TOKEN)


# # utils/balebot/pakage_development/process_update.py
# import logging
# import aiohttp
# from balethon import Client
# from balethon.objects import Message, CallbackQuery, User, Chat
# from typing import Callable, Optional, Dict, Any, Union
# from utils.variables.TOKEN import BTOKEN as TOKEN
# import asyncio
# import traceback

# logger = logging.getLogger(__name__)

# BOT_API_IP = "2.189.68.126"
# HEADERS = {"Host": "tapi.bale.ai"}


# # ================================================
# # کلاس‌های ساده (کارآمد برای حافظه)
# # ================================================

# class SimpleUser:
#     __slots__ = ('id', 'first_name', 'last_name', 'username', 'is_bot', 'language_code', 'from_user')
#     def __init__(self, data):
#         self.id = data.get('id')
#         self.first_name = data.get('first_name', '')
#         self.last_name = data.get('last_name', '')
#         self.username = data.get('username', '')
#         self.is_bot = data.get('is_bot', False)
#         self.language_code = data.get('language_code', '')
#         self.from_user = data.get('from_user', '')


# class SimpleChat:
#     __slots__ = ('id', 'type', 'first_name', 'last_name', 'username', 'title')
#     def __init__(self, data):
#         self.id = data.get('id')
#         self.type = data.get('type', 'private')
#         self.first_name = data.get('first_name', '')
#         self.last_name = data.get('last_name', '')
#         self.username = data.get('username', '')
#         self.title = data.get('title', '')


# # ================================================
# # کلاس Message Proxy که از Message بالیتون ارث‌بری می‌کند
# # ================================================

# class SimpleMessage(Message):
#     """
#     کلاس پیام سفارشی که هم از Message بالیتون ارث‌بری می‌کند
#     و هم با دیتای خام بله کار می‌کند
#     """
#     __slots__ = ('_raw', '_bot_instance', '_simple_user', '_simple_chat')
    
#     def __init__(self, data, bot_instance=None):
#         # ذخیره دیتای خام
#         self._raw = data
#         self._bot_instance = bot_instance
        
#         # ساخت اشیاء ساده برای دسترسی سریع
#         from_data = data.get('from', {})
#         self._simple_user = SimpleUser(from_data)
        
#         chat_data = data.get('chat', {})
#         self._simple_chat = SimpleChat(chat_data)
        
#         # فراخوانی سازنده Message بالیتون با پارامترهای صحیح
#         super().__init__(
#             message_id=data.get('message_id'),
#             date=data.get('date'),
#             text=data.get('text', ''),
#             chat=self._simple_chat,
#             from_user=self._simple_user,
#             bot=bot_instance,
#             raw=data
#         )
    
#     @property
#     def chat(self):
#         return self._simple_chat
    
#     @property
#     def from_user(self):
#         return self._simple_user
    
#     @property
#     def author(self):
#         return self._simple_user
    
#     async def reply(self, text: str, reply_markup=None, **kwargs):
#         if self._bot_instance:
#             return await self._bot_instance.send_message_direct(
#                 chat_id=self.chat.id,
#                 text=text,
#                 reply_markup=reply_markup
#             )
#         return await super().reply(text, reply_markup=reply_markup)
    
#     async def send_message(self, text: str, reply_markup: Any = None, **kwargs):
#         return await self.reply(text, reply_markup=reply_markup)


# # ================================================
# # کلاس CallbackQuery Proxy
# # ================================================

# class SimpleCallbackQuery(CallbackQuery):
#     """کلاس callback_query سفارشی که از CallbackQuery بالیتون ارث‌بری می‌کند"""
#     __slots__ = ('_raw', '_bot_instance', '_simple_from', '_simple_message')
    
#     def __init__(self, data, bot_instance=None):
#         self._raw = data
#         self._bot_instance = bot_instance
        
#         from_data = data.get('from', {})
#         self._simple_from = SimpleUser(from_data)
        
#         message_data = data.get('message', {})
#         self._simple_message = SimpleMessage(message_data, bot_instance) if message_data else None
        
#         super().__init__(
#             id=data.get('id'),
#             from_user=self._simple_from,
#             message=self._simple_message,
#             data=data.get('data', ''),
#             bot=bot_instance,
#             raw=data
#         )
    
#     async def answer(self, text: str = None, show_alert: bool = False, **kwargs):
#         if self._bot_instance and hasattr(self._bot_instance, 'answer_callback_direct'):
#             return await self._bot_instance.answer_callback_direct(
#                 callback_query_id=self.id,
#                 text=text,
#                 show_alert=show_alert
#             )
#         return await super().answer(text, show_alert=show_alert)


# # ================================================
# # کلاس اصلی ربات
# # ================================================

# class MyCustomBot(Client):
#     """کلاس سفارشی ربات با قابلیت پردازش وب‌هوک"""
    
#     def __init__(self, token, *args, **kwargs):
#         super().__init__(token, *args, **kwargs)
#         self.command_handlers = {}
#         self.message_handlers = []
#         self.callback_handlers = []
#         self.custom_token = token
#         self._session = None
#         self._connector = None
#         self._session_lock = asyncio.Lock()
        
#     async def _get_session(self):
#         if self._session is None or self._session.closed:
#             async with self._session_lock:
#                 if self._session is None or self._session.closed:
#                     timeout = aiohttp.ClientTimeout(total=30, connect=10)
#                     self._connector = aiohttp.TCPConnector(
#                         limit=100,
#                         limit_per_host=50,
#                         ttl_dns_cache=300,
#                         enable_cleanup_closed=True
#                     )
#                     self._session = aiohttp.ClientSession(
#                         connector=self._connector,
#                         headers=HEADERS,
#                         timeout=timeout
#                     )
#         return self._session
    
#     async def close(self):
#         if self._session and not self._session.closed:
#             await self._session.close()
#         if self._connector and not self._connector.closed:
#             await self._connector.close()

#     async def send_message_direct(
#         self, 
#         chat_id: int, 
#         text: str, 
#         parse_mode: str = "Markdown",
#         reply_markup: Any = None
#     ):
#         url = f"https://{BOT_API_IP}/bot{self.custom_token}/sendMessage"
#         payload = {
#             "chat_id": chat_id,
#             "text": text,
#             "parse_mode": parse_mode
#         }
        
#         if reply_markup:
#             if hasattr(reply_markup, 'to_dict'):
#                 payload["reply_markup"] = reply_markup.to_dict()
#             elif hasattr(reply_markup, 'keyboard'):
#                 keyboard_rows = []
#                 for row in reply_markup.keyboard:
#                     button_row = []
#                     for btn in row:
#                         button_row.append({"text": btn.text})
#                     keyboard_rows.append(button_row)
#                 payload["reply_markup"] = {
#                     "keyboard": keyboard_rows,
#                     "resize_keyboard": getattr(reply_markup, 'resize_keyboard', True),
#                     "one_time_keyboard": getattr(reply_markup, 'one_time_keyboard', False)
#                 }
#             elif hasattr(reply_markup, 'inline_keyboard'):
#                 keyboard_rows = []
#                 for row in reply_markup.inline_keyboard:
#                     button_row = []
#                     for btn in row:
#                         button_row.append({
#                             "text": btn.text,
#                             "callback_data": getattr(btn, 'callback_data', None),
#                             "url": getattr(btn, 'url', None)
#                         })
#                     keyboard_rows.append(button_row)
#                 payload["reply_markup"] = {"inline_keyboard": keyboard_rows}
#             else:
#                 payload["reply_markup"] = reply_markup

#         for attempt in range(3):
#             try:
#                 session = await self._get_session()
#                 async with session.post(url, json=payload, ssl=False) as response:
#                     if response.status == 200:
#                         result = await response.json()
#                         if result.get('ok'):
#                             logger.info(f"Message sent to {chat_id}")
#                             return result
#                     else:
#                         logger.warning(f"Send failed with status {response.status}")
#             except RuntimeError as e:
#                 if "Event loop is closed" in str(e):
#                     logger.warning(f"Event loop closed, recreating session (attempt {attempt + 1})")
#                     self._session = None
#                     self._connector = None
#                     await asyncio.sleep(0.1 * (attempt + 1))
#                     continue
#                 logger.error(f"Runtime error: {e}")
#             except Exception as e:
#                 logger.error(f"Send error: {e}")
            
#             if attempt < 2:
#                 await asyncio.sleep(0.1 * (attempt + 1))
        
#         return None

#     async def answer_callback_direct(self, callback_query_id: str, text: str = None, show_alert: bool = False):
#         """پاسخ مستقیم به callback_query"""
#         url = f"https://{BOT_API_IP}/bot{self.custom_token}/answerCallbackQuery"
#         payload = {
#             "callback_query_id": callback_query_id,
#             "text": text or "",
#             "show_alert": show_alert
#         }
        
#         try:
#             session = await self._get_session()
#             async with session.post(url, json=payload, ssl=False) as response:
#                 if response.status == 200:
#                     result = await response.json()
#                     return result.get('ok', False)
#         except Exception as e:
#             logger.error(f"Answer callback error: {e}")
#         return False

#     def on_message(self, condition: Optional[Callable] = None):
#         def decorator(func: Callable):
#             self.message_handlers.append({"func": func, "condition": condition})
#             return func
#         return decorator

#     def on_command(self, command_name: str):
#         def decorator(func: Callable):
#             self.command_handlers[command_name] = func
#             return func
#         return decorator
    
#     def on_callback_query(self, condition: Optional[Callable] = None):
#         def decorator(func: Callable):
#             self.callback_handlers.append({"func": func, "condition": condition})
#             return func
#         return decorator

#     async def process_update(self, update_data: Dict[str, Any]):
#         """پردازش آپدیت - برگرداندن اشیاء ارث‌برده از Message و CallbackQuery"""
#         try:
#             # پیام
#             if 'message' in update_data:
#                 # ✅ ایجاد message با دو پارامتر (data, bot_instance)
#                 message = SimpleMessage(update_data['message'], self)
#                 text = message.text or ""
                
#                 # دستورات
#                 if text and text.startswith('/'):
#                     command_name = text.split()[0][1:].split('@')[0]
#                     if command_name in self.command_handlers:
#                         await self.command_handlers[command_name](message)
#                         return
                
#                 # هندلرهای عمومی
#                 for handler in self.message_handlers:
#                     condition = handler.get("condition")
#                     if condition is None:
#                         await handler["func"](message)
#                         return
#                     elif callable(condition):
#                         try:
#                             if asyncio.iscoroutinefunction(condition):
#                                 result = await condition(message)
#                             else:
#                                 result = condition(message)
#                             if result:
#                                 await handler["func"](message)
#                                 return
#                         except Exception as e:
#                             logger.debug(f"Condition failed: {e}")
            
#             # callback_query
#             elif 'callback_query' in update_data:
#                 callback = SimpleCallbackQuery(update_data['callback_query'], self)
                
#                 for handler in self.callback_handlers:
#                     condition = handler.get("condition")
#                     if condition is None:
#                         await handler["func"](callback)
#                         return
#                     elif callable(condition):
#                         try:
#                             if asyncio.iscoroutinefunction(condition):
#                                 result = await condition(callback)
#                             else:
#                                 result = condition(callback)
#                             if result:
#                                 await handler["func"](callback)
#                                 return
#                         except Exception as e:
#                             logger.debug(f"Callback condition failed: {e}")
                            
#         except Exception as e:
#             logger.error(f"Error in process_update: {traceback.format_exc()}")


# # ایجاد نمونه سراسری
# bot = MyCustomBot(TOKEN)



# utils/balebot/pakage_development/process_update.py
import logging
import aiohttp
from balethon import Client
from typing import Callable, Optional, Dict, Any, Union
from utils.variables.TOKEN import BTOKEN as TOKEN
import asyncio
import traceback

logger = logging.getLogger(__name__)

BOT_API_IP = "2.189.68.126"
HEADERS = {"Host": "tapi.bale.ai"}


# ================================================
# کلاس‌های ساده (کارآمد برای حافظه)
# ================================================

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


# ================================================
# کلاس Message - بدون ارث‌بری از بالیتون
# ================================================

class SimpleMessage:
    """
    کلاس پیام سفارشی - بدون ارث‌بری از Message بالیتون
    اما با متدهای مورد نیاز برای سازگاری
    """
    __slots__ = ('_raw', '_bot', 'message_id', 'date', 'text', 'chat', 'from_user', 'author')
    
    def __init__(self, data, bot_instance):
        self._raw = data
        self._bot = bot_instance
        
        self.message_id = data.get('message_id')
        self.date = data.get('date')
        self.text = data.get('text', '')
        
        from_data = data.get('from', {})
        self.from_user = SimpleUser(from_data)
        self.author = self.from_user
        
        chat_data = data.get('chat', {})
        self.chat = SimpleChat(chat_data)
    
    async def reply(self, text: str, reply_markup=None, **kwargs):
        return await self._bot.send_message_direct(
            chat_id=self.chat.id,
            text=text,
            reply_markup=reply_markup
        )
    
    async def send_message(self, text: str, reply_markup=None, **kwargs):
        return await self.reply(text, reply_markup=reply_markup)


# ================================================
# کلاس CallbackQuery - بدون ارث‌بری از بالیتون
# ================================================

class SimpleCallbackQuery:
    """کلاس callback_query سفارشی"""
    __slots__ = ('_raw', '_bot', 'id', 'from_user', 'message', 'data')
    
    def __init__(self, data, bot_instance):
        self._raw = data
        self._bot = bot_instance
        
        self.id = data.get('id')
        
        from_data = data.get('from', {})
        self.from_user = SimpleUser(from_data)
        
        message_data = data.get('message', {})
        self.message = SimpleMessage(message_data, bot_instance) if message_data else None
        
        self.data = data.get('data', '')
    
    async def answer(self, text: str = None, show_alert: bool = False, **kwargs):
        if hasattr(self._bot, 'answer_callback_direct'):
            return await self._bot.answer_callback_direct(
                callback_query_id=self.id,
                text=text,
                show_alert=show_alert
            )
        return None


# ================================================
# کلاس اصلی ربات
# ================================================

class MyCustomBot(Client):
    """کلاس سفارشی ربات با قابلیت پردازش وب‌هوک"""
    
    def __init__(self, token, *args, **kwargs):
        super().__init__(token, *args, **kwargs)
        self.command_handlers = {}
        self.message_handlers = []
        self.callback_handlers = []
        self.custom_token = token
        self._session = None
        self._connector = None
        self._session_lock = asyncio.Lock()
        
    async def _get_session(self):
        if self._session is None or self._session.closed:
            async with self._session_lock:
                if self._session is None or self._session.closed:
                    timeout = aiohttp.ClientTimeout(total=30, connect=10)
                    self._connector = aiohttp.TCPConnector(
                        limit=100,
                        limit_per_host=50,
                        ttl_dns_cache=300,
                        enable_cleanup_closed=True
                    )
                    self._session = aiohttp.ClientSession(
                        connector=self._connector,
                        headers=HEADERS,
                        timeout=timeout
                    )
        return self._session
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
        if self._connector and not self._connector.closed:
            await self._connector.close()

    async def send_message_direct(
        self, 
        chat_id: int, 
        text: str, 
        parse_mode: str = "Markdown",
        reply_markup: Any = None
    ):
        url = f"https://{BOT_API_IP}/bot{self.custom_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        
        if reply_markup:
            if hasattr(reply_markup, 'to_dict'):
                payload["reply_markup"] = reply_markup.to_dict()
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
            elif hasattr(reply_markup, 'inline_keyboard'):
                keyboard_rows = []
                for row in reply_markup.inline_keyboard:
                    button_row = []
                    for btn in row:
                        button_row.append({
                            "text": btn.text,
                            "callback_data": getattr(btn, 'callback_data', None),
                            "url": getattr(btn, 'url', None)
                        })
                    keyboard_rows.append(button_row)
                payload["reply_markup"] = {"inline_keyboard": keyboard_rows}
            else:
                payload["reply_markup"] = reply_markup

        for attempt in range(3):
            try:
                session = await self._get_session()
                async with session.post(url, json=payload, ssl=False) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            logger.info(f"Message sent to {chat_id}")
                            return result
                    else:
                        logger.warning(f"Send failed with status {response.status}")
            except RuntimeError as e:
                if "Event loop is closed" in str(e):
                    logger.warning(f"Event loop closed, recreating session (attempt {attempt + 1})")
                    self._session = None
                    self._connector = None
                    await asyncio.sleep(0.1 * (attempt + 1))
                    continue
                logger.error(f"Runtime error: {e}")
            except Exception as e:
                logger.error(f"Send error: {e}")
            
            if attempt < 2:
                await asyncio.sleep(0.1 * (attempt + 1))
        
        return None

    async def answer_callback_direct(self, callback_query_id: str, text: str = None, show_alert: bool = False):
        """پاسخ مستقیم به callback_query"""
        url = f"https://{BOT_API_IP}/bot{self.custom_token}/answerCallbackQuery"
        payload = {
            "callback_query_id": callback_query_id,
            "text": text or "",
            "show_alert": show_alert
        }
        
        try:
            session = await self._get_session()
            async with session.post(url, json=payload, ssl=False) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('ok', False)
        except Exception as e:
            logger.error(f"Answer callback error: {e}")
        return False

    def on_message(self, condition: Optional[Callable] = None):
        def decorator(func: Callable):
            self.message_handlers.append({"func": func, "condition": condition})
            return func
        return decorator

    def on_command(self, command_name: str):
        def decorator(func: Callable):
            self.command_handlers[command_name] = func
            return func
        return decorator
    
    def on_callback_query(self, condition: Optional[Callable] = None):
        def decorator(func: Callable):
            self.callback_handlers.append({"func": func, "condition": condition})
            return func
        return decorator

    async def process_update(self, update_data: Dict[str, Any]):
        """پردازش آپدیت - برگرداندن اشیاء ساده"""
        try:
            # پیام
            if 'message' in update_data:
                message = SimpleMessage(update_data['message'], self)
                text = message.text or ""
                
                # دستورات
                if text and text.startswith('/'):
                    command_name = text.split()[0][1:].split('@')[0]
                    if command_name in self.command_handlers:
                        await self.command_handlers[command_name](message)
                        return
                
                # هندلرهای عمومی
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
            
            # callback_query
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


# ایجاد نمونه سراسری
bot = MyCustomBot(TOKEN)