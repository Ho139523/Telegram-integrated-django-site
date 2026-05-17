#    # utils/balebot/decorators.py
#    import traceback
#    from functools import wraps
#    from typing import List, Union, Optional
#    from telbot.sessions import session_manager
#    
#    
#    def _extract_message_id(obj) -> Optional[int]:
    #    """استخراج message_id از اشیاء مختلف"""
    #    if hasattr(obj, 'message_id'):
        #    return obj.message_id
    #    elif isinstance(obj, dict) and obj.get("message_id"):
        #    return obj["message_id"]
    #    elif isinstance(obj, int):
        #    return obj
    #    return None
#    
#    
#    def _extract_message_ids(obj) -> List[int]:
    #    """استخراج لیست message_id از اشیاء مختلف"""
    #    message_ids = []
    #    
    #    if obj is None:
        #    return message_ids
    #    
    #    # اگر لیست است
    #    if isinstance(obj, (list, tuple)):
        #    for item in obj:
            #    msg_id = _extract_message_id(item)
            #    if msg_id:
                #    message_ids.append(msg_id)
    #    else:
        #    msg_id = _extract_message_id(obj)
        #    if msg_id:
            #    message_ids.append(msg_id)
    #    
    #    return message_ids
#    
#    
#    def clear_previous_messages(keep_last: int = 2, namespace: str = "default"):
    #    """
    #    دکوراتور پویا برای مدیریت پیام‌ها و پاک کردن پیام‌های قبلی
    #    
    #    Args:
        #    keep_last: تعداد پیام‌هایی که باید نگهداری شوند (پیش‌فرض 2)
                   #    - اگر 1 باشد: فقط پیام جدید کاربر نگهداری می‌شود
                   #    - اگر 2 باشد: پیام جدید کاربر + 1 پاسخ آخر ربات
                   #    - اگر 3 باشد: پیام جدید کاربر + 2 پاسخ آخر ربات
                   #    - اگر 0 باشد: همه پیام‌ها حذف می‌شوند
        #    
        #    namespace: namespace سشن (پیش‌فرض "default")
    #    
    #    نحوه کار:
        #    - پیام قبلی کاربر حذف می‌شود
        #    - N-1 پیام قبلی ربات حذف می‌شوند (N = keep_last)
        #    - پیام جدید کاربر ذخیره می‌شود
        #    - تابع اصلی اجرا می‌شود
        #    - پیام‌های جدید ربات ذخیره می‌شوند
    #    """
    #    def decorator(func):
        #    @wraps(func)
        #    async def wrapper(message, *args, **kwargs):
            #    chat_id = message.chat.id
            #    
            #    try:
                #    session = session_manager.get_user_session(chat_id, namespace=namespace)
                #    
                #    # 1. حذف پیام قبلی کاربر
                #    previous_user_msg_id = session.get("last_user_message_id")
                #    if previous_user_msg_id:
                    #    try:
                        #    await message._bot.delete_message(chat_id, previous_user_msg_id)
                        #    print(f"Deleted previous user message: {previous_user_msg_id}")
                    #    except Exception as e:
                        #    print(f"Error deleting previous user message: {e}")
                #    
                #    # 2. حذف پیام‌های قبلی ربات (به جز keep_last-1 تا آخرین)
                #    previous_bot_msg_ids = session.get("last_bot_message_ids", [])
                #    
                #    # تعداد پیام‌هایی که باید نگهداری شوند (حداکثر keep_last-1)
                #    keep_bot_count = max(0, keep_last - 1)
                #    
                #    # پیام‌هایی که باید حذف شوند
                #    messages_to_delete = previous_bot_msg_ids[:-keep_bot_count] if keep_bot_count > 0 else previous_bot_msg_ids
                #    
                #    for msg_id in messages_to_delete:
                    #    try:
                        #    await message._bot.delete_message(chat_id, msg_id)
                        #    print(f"Deleted previous bot message: {msg_id}")
                    #    except Exception as e:
                        #    print(f"Error deleting previous bot message {msg_id}: {e}")
                #    
                #    # پیام‌هایی که باید نگهداری شوند
                #    kept_messages = previous_bot_msg_ids[-keep_bot_count:] if keep_bot_count > 0 else []
                #    
                #    # 3. ذخیره پیام جدید کاربر
                #    session["last_user_message_id"] = message.message_id
                #    
                #    # 4. اجرای تابع اصلی
                #    result = await func(message, *args, **kwargs)
                #    
                #    # 5. استخراج و ذخیره پیام‌های جدید ربات
                #    new_bot_message_ids = _extract_message_ids(result)
                #    
                #    # ترکیب پیام‌های نگهداری شده با پیام‌های جدید
                #    all_bot_messages = kept_messages + new_bot_message_ids
                #    
                #    # ذخیره لیست پیام‌های ربات
                #    session["last_bot_message_ids"] = all_bot_messages
                #    
                #    # ذخیره سشن
                #    session_manager.set_user_session(chat_id, session, namespace=namespace)
                #    
                #    print(f"Keep last: {keep_last}, Kept bot messages: {len(kept_messages)}, New bot messages: {len(new_bot_message_ids)}, Total bot messages: {len(all_bot_messages)}")
                #    
                #    return result
                #    
            #    except Exception as e:
                #    print(f"Error in clear_previous_messages decorator: {traceback.format_exc()}")
                #    return await func(message, *args, **kwargs)
        #    
        #    return wrapper
    #    return decorator
#    
#    
#    # نسخه ساده با keep_last پیش‌فرض 2
#    def auto_clear(func):
    #    """دکوراتور ساده برای پاک کردن خودکار پیام‌ها (نگهداری 2 پیام آخر)"""
    #    return clear_previous_messages(keep_last=2)(func)
#    
#    
#    # نسخه با قابلیت تنظیم تعداد
#    def keep_messages(keep_last: int = 2):
    #    """
    #    دکوراتور با قابلیت تنظیم تعداد پیام‌های نگهداری شده
    #    
    #    Args:
        #    keep_last: تعداد پیام‌هایی که باید نگهداری شوند
                   #    - 1: فقط پیام جدید کاربر
                   #    - 2: پیام جدید کاربر + 1 پاسخ ربات
                   #    - 3: پیام جدید کاربر + 2 پاسخ ربات
                   #    - و ...
    #    """
    #    return clear_previous_messages(keep_last=keep_last)


# utils/balebot/decorators.py
import traceback
from functools import wraps
from typing import List, Optional, Union
from telbot.sessions import session_manager


def _extract_message_id(obj) -> Optional[int]:
    """استخراج message_id از اشیاء مختلف"""
    if hasattr(obj, 'message_id'):
        return obj.message_id
    elif isinstance(obj, dict) and obj.get("message_id"):
        return obj["message_id"]
    elif isinstance(obj, int):
        return obj
    return None


def _extract_message_ids(obj) -> List[int]:
    """استخراج لیست message_id از اشیاء مختلف"""
    message_ids = []

    if obj is None:
        return message_ids

    if isinstance(obj, (list, tuple)):
        for item in obj:
            msg_id = _extract_message_id(item)
            if msg_id:
                message_ids.append(msg_id)
    else:
        msg_id = _extract_message_id(obj)
        if msg_id:
            message_ids.append(msg_id)

    return message_ids


def _get_message_from_event(event):
    """استخراج message از رویداد (Message یا CallbackQuery)"""
    if hasattr(event, 'message') and hasattr(event, 'chat') is False:
        # CallbackQuery
        return event.message
    else:
        # Message
        return event


def _get_chat_id_from_event(event):
    """استخراج chat_id از رویداد (Message یا CallbackQuery)"""
    if hasattr(event, 'message') and hasattr(event, 'chat') is False:
        # CallbackQuery
        return event.message.chat.id
    else:
        # Message
        return event.chat.id


def _get_bot_from_event(event):
    """استخراج bot از رویداد"""
    if hasattr(event, '_bot'):
        return event._bot
    elif hasattr(event, 'message') and hasattr(event.message, '_bot'):
        return event.message._bot
    return None


def clear_previous_messages(namespace: str = "default"):
    """
    دکوراتور برای مدیریت پیام‌ها و پاک کردن پیام‌های قبلی کاربر و ربات
    سازگار با Message و CallbackQuery

    Args:
        namespace: namespace سشن (پیش‌فرض "default")
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(event, *args, **kwargs):
            # استخراج اطلاعات از رویداد
            message = _get_message_from_event(event)
            chat_id = _get_chat_id_from_event(event)
            bot = _get_bot_from_event(event) or getattr(message, '_bot', None)

            try:
                session = session_manager.get_user_session(chat_id, namespace=namespace)

                # 1. حذف پیام قبلی کاربر
                previous_user_msg_id = session.get("last_user_message_id")
                if previous_user_msg_id:
                    try:
                        await bot.delete_message(chat_id, previous_user_msg_id)
                        print(f"Deleted previous user message: {previous_user_msg_id}")
                    except Exception as e:
                        print(f"Error deleting previous user message: {e}")

                # 2. حذف پیام قبلی ربات
                previous_bot_msg_id = session.get("last_bot_message_id")
                if previous_bot_msg_id:
                    try:
                        await bot.delete_message(chat_id, previous_bot_msg_id)
                        print(f"Deleted previous bot message: {previous_bot_msg_id}")
                    except Exception as e:
                        print(f"Error deleting previous bot message: {e}")

                # 3. ذخیره پیام جدید کاربر
                session["last_user_message_id"] = message.message_id

                # 4. اجرای تابع اصلی
                result = await func(event, *args, **kwargs)

                # 5. ذخیره پیام جدید ربات
                if result:
                    if hasattr(result, 'message_id'):
                        session["last_bot_message_id"] = result.message_id
                        print(f"Saved new bot message: {result.message_id}")
                    elif isinstance(result, dict) and result.get("message_id"):
                        session["last_bot_message_id"] = result["message_id"]
                        print(f"Saved new bot message: {result['message_id']}")
                    elif isinstance(result, int):
                        session["last_bot_message_id"] = result
                        print(f"Saved new bot message: {result}")

                session_manager.set_user_session(chat_id, session, namespace=namespace)
                return result

            except Exception as e:
                print(f"Error in clear_previous_messages decorator: {traceback.format_exc()}")
                return await func(event, *args, **kwargs)

        return wrapper
    return decorator


def auto_clear(func):
    """دکوراتور ساده برای پاک کردن خودکار پیام‌های قبلی - سازگار با Message و CallbackQuery"""
    @wraps(func)
    async def wrapper(event, *args, **kwargs):
        # استخراج اطلاعات از رویداد
        message = _get_message_from_event(event)
        chat_id = _get_chat_id_from_event(event)
        bot = _get_bot_from_event(event) or getattr(message, '_bot', None)
        namespace = "auto_clear"

        try:
            session = session_manager.get_user_session(chat_id, namespace=namespace)

            print(f"=== AUTO CLEAR START ===")
            print(f"Chat ID: {chat_id}")
            print(f"Current message ID: {message.message_id}")

            # حذف پیام قبلی ربات
            last_bot_msg = session.get("last_bot_message_id")
            if last_bot_msg:
                try:
                    result = await bot.delete_message(chat_id, last_bot_msg)
                    if result:
                        print(f"✅ Deleted previous bot message: {last_bot_msg}")
                except Exception as e:
                    print(f"Error deleting bot message: {e}")

            # حذف پیام قبلی کاربر
            last_user_msg = session.get("last_user_message_id")
            if last_user_msg and last_user_msg != message.message_id:
                try:
                    result = await bot.delete_message(chat_id, last_user_msg)
                    if result:
                        print(f"✅ Deleted previous user message: {last_user_msg}")
                except Exception as e:
                    print(f"Error deleting user message: {e}")

            # ذخیره پیام جدید کاربر
            session["last_user_message_id"] = message.message_id

            # اجرای تابع اصلی
            result = await func(event, *args, **kwargs)

            # ذخیره پیام جدید ربات
            if result:
                if hasattr(result, 'message_id'):
                    session["last_bot_message_id"] = result.message_id
                    print(f"✅ Saved new bot message: {result.message_id}")
                elif isinstance(result, dict) and result.get("message_id"):
                    session["last_bot_message_id"] = result["message_id"]
                    print(f"✅ Saved new bot message: {result['message_id']}")

            session_manager.set_user_session(chat_id, session, namespace=namespace)
            return result

        except Exception as e:
            print(f"Auto clear error: {traceback.format_exc()}")
            return await func(event, *args, **kwargs)

    return wrapper


def store_messages(max_messages: int = 100, namespace: str = "stored_messages"):
    """دکوراتور برای ذخیره message_id پیام‌های ارسالی - سازگار با Message و CallbackQuery"""
    def decorator(func):
        @wraps(func)
        async def wrapper(event, *args, **kwargs):
            chat_id = _get_chat_id_from_event(event)

            try:
                result = await func(event, *args, **kwargs)
                new_message_ids = _extract_message_ids(result)

                if new_message_ids:
                    session = session_manager.get_user_session(chat_id, namespace=namespace)
                    stored_messages = session.get("message_ids", [])
                    stored_messages.extend(new_message_ids)

                    if len(stored_messages) > max_messages:
                        stored_messages = stored_messages[-max_messages:]

                    session["message_ids"] = stored_messages
                    session["total_count"] = len(stored_messages)
                    session_manager.set_user_session(chat_id, session, namespace=namespace)

                    print(f"📝 Stored {len(new_message_ids)} messages. Total: {len(stored_messages)}/{max_messages}")

                return result

            except Exception as e:
                print(f"Error in store_messages: {traceback.format_exc()}")
                return await func(event, *args, **kwargs)

        return wrapper
    return decorator


async def clear_stored_messages(
    event,
    namespace: str = "stored_messages",
    keep_last: int = 0,
    delete_user_message: bool = False
) -> int:
    """
    حذف تمام پیام‌های ذخیره شده - سازگار با Message و CallbackQuery

    Args:
        event: Message یا CallbackQuery
        namespace: namespace سشن
        keep_last: تعداد پیام‌هایی که باید نگهداری شوند
        delete_user_message: آیا پیام کاربر نیز حذف شود

    Returns:
        int: تعداد پیام‌های حذف شده
    """
    message = _get_message_from_event(event)
    chat_id = _get_chat_id_from_event(event)
    bot = _get_bot_from_event(event) or getattr(message, '_bot', None)
    deleted_count = 0

    try:
        session = session_manager.get_user_session(chat_id, namespace=namespace)
        stored_messages = session.get("message_ids", [])

        if not stored_messages:
            return 0

        if keep_last > 0:
            messages_to_delete = stored_messages[:-keep_last]
            messages_to_keep = stored_messages[-keep_last:]
        else:
            messages_to_delete = stored_messages
            messages_to_keep = []

        for msg_id in messages_to_delete:
            try:
                await bot.delete_message(chat_id, msg_id)
                deleted_count += 1
            except Exception as e:
                print(f"Error deleting message {msg_id}: {e}")

        session["message_ids"] = messages_to_keep
        session["total_count"] = len(messages_to_keep)
        session_manager.set_user_session(chat_id, session, namespace=namespace)

        if delete_user_message:
            try:
                await bot.delete_message(chat_id, message.message_id)
            except Exception as e:
                print(f"Error deleting user message: {e}")

        return deleted_count

    except Exception as e:
        print(f"Error in clear_stored_messages: {traceback.format_exc()}")
        return 0


def clear_messages_on_command(namespace: str = "stored_messages", keep_last: int = 0):
    """
    دکوراتور برای پاک کردن خودکار پیام‌های ذخیره شده قبل از اجرای هندلر
    سازگار با Message و CallbackQuery
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(event, *args, **kwargs):
            await clear_stored_messages(event, namespace=namespace, keep_last=keep_last)
            result = await func(event, *args, **kwargs)
            return result
        return wrapper
    return decorator


def clear_messages(keep_last: int = 2, namespace: str = "default"):
    """
    دکوراتور پیشرفته برای مدیریت پیام‌ها - سازگار با Message و CallbackQuery
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(event, *args, **kwargs):
            message = _get_message_from_event(event)
            chat_id = _get_chat_id_from_event(event)
            bot = _get_bot_from_event(event) or getattr(message, '_bot', None)

            try:
                session = session_manager.get_user_session(chat_id, namespace=namespace)
                previous_messages = session.get("message_history", [])

                for msg_id in previous_messages[:-keep_last] if keep_last > 0 else previous_messages:
                    try:
                        await bot.delete_message(chat_id, msg_id)
                    except:
                        pass

                new_history = previous_messages[-keep_last:] if keep_last > 0 else []
                new_history.append(message.message_id)

                result = await func(event, *args, **kwargs)

                if result:
                    if hasattr(result, 'message_id'):
                        new_history.append(result.message_id)
                    elif isinstance(result, dict) and result.get("message_id"):
                        new_history.append(result["message_id"])
                    elif isinstance(result, int):
                        new_history.append(result)

                session["message_history"] = new_history
                session_manager.set_user_session(chat_id, session, namespace=namespace)
                return result

            except Exception as e:
                print(f"Error in clear_messages: {e}")
                return await func(event, *args, **kwargs)

        return wrapper
    return decorator


async def add_to_stored_messages(event, message_result, namespace: str = "stored_messages", max_messages: int = 100):
    """اضافه کردن پیام به لیست ذخیره شده - سازگار با Message و CallbackQuery"""
    chat_id = _get_chat_id_from_event(event)
    msg_id = _extract_message_id(message_result)

    if msg_id:
        session = session_manager.get_user_session(chat_id, namespace=namespace)
        stored_messages = session.get("message_ids", [])
        stored_messages.append(msg_id)

        if len(stored_messages) > max_messages:
            stored_messages = stored_messages[-max_messages:]

        session["message_ids"] = stored_messages
        session["total_count"] = len(stored_messages)
        session_manager.set_user_session(chat_id, session, namespace=namespace)
        return True

    return False


async def get_stored_messages_count(event, namespace: str = "stored_messages") -> int:
    """دریافت تعداد پیام‌های ذخیره شده"""
    chat_id = _get_chat_id_from_event(event)
    session = session_manager.get_user_session(chat_id, namespace=namespace)
    return session.get("total_count", 0)


async def get_stored_messages_ids(event, namespace: str = "stored_messages") -> List[int]:
    """دریافت لیست پیام‌های ذخیره شده"""
    chat_id = _get_chat_id_from_event(event)
    session = session_manager.get_user_session(chat_id, namespace=namespace)
    return session.get("message_ids", [])
