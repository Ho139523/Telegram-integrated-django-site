import traceback
from functools import wraps
from typing import List, Optional, Union
from telbot.sessions import session_manager
from telbot.views import app

def clear_previous_messages(namespace: str = "default"):

    """

    دکوراتور برای مدیریت پیام‌ها و پاک کردن پیام‌های قبلی کاربر و ربات

    سازگار با Message و CallbackQuery



    Args:

        namespace: namespace سشن (پیش‌فرض "default")

    """

    def decorator(func):

        @wraps(func)

        def wrapper(event, *args, **kwargs):

            # استخراج اطلاعات از رویداد

            message = _get_message_from_event(event)

            chat_id = _get_chat_id_from_event(event)

            bot = app



            try:

                session = session_manager.get_user_session(chat_id, namespace=namespace)



                # 1. حذف پیام قبلی کاربر

                previous_user_msg_id = session.get("last_user_message_id")

                if previous_user_msg_id:

                    try:

                        bot.delete_message(chat_id, previous_user_msg_id)

                        print(f"Deleted previous user message: {previous_user_msg_id}")

                    except Exception as e:

                        print(f"Error deleting previous user message: {e}")



                # 2. حذف پیام قبلی ربات

                previous_bot_msg_id = session.get("last_bot_message_id")

                if previous_bot_msg_id:

                    try:

                        bot.delete_message(chat_id, previous_bot_msg_id)

                        print(f"Deleted previous bot message: {previous_bot_msg_id}")

                    except Exception as e:

                        print(f"Error deleting previous bot message: {e}")



                # 3. ذخیره پیام جدید کاربر

                session["last_user_message_id"] = message.message_id



                # 4. اجرای تابع اصلی

                result = func(event, *args, **kwargs)



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

                return func(event, *args, **kwargs)



        return wrapper

    return decorator





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



