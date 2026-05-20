# utils/balebot/ClassBase.py
import traceback
from typing import Dict, Optional
from balethon.objects import Message, CallbackQuery
from utils.balebot.decorators import store_messages, clear_previous_messages, clear_messages_on_command, auto_clear
from utils.balebot.helpers import t, get_profile
from telbot.sessions import session_manager
from utils.balebot.handlers import home_handler


# ================================================
# کلاس مدیریت چت پشتیبانی
# ================================================

class SupportChatManager:
    """مدیریت چت‌های پشتیبانی"""
    
    SUPPORT_NAMESPACE = "support_chat"
    PENDING_MESSAGES_NAMESPACE = "pending_messages"
    
    @classmethod
    def get_support_session(cls, chat_id: int) -> dict:
        """دریافت سشن پشتیبانی کاربر"""
        return session_manager.get_user_session(chat_id, namespace=cls.SUPPORT_NAMESPACE)
    
    @classmethod
    def set_support_session(cls, chat_id: int, session: dict):
        """ذخیره سشن پشتیبانی کاربر"""
        session_manager.set_user_session(chat_id, session, namespace=cls.SUPPORT_NAMESPACE)
    
    @classmethod
    def clear_support_session(cls, chat_id: int):
        """پاک کردن سشن پشتیبانی کاربر"""
        session_manager.delete(chat_id, namespace=cls.SUPPORT_NAMESPACE)
    
    @classmethod
    def is_support_mode(cls, chat_id: int) -> bool:
        """بررسی اینکه کاربر در حالت پشتیبانی است"""
        session = cls.get_support_session(chat_id)
        return session.get("support_mode", False)
    
    @classmethod
    def set_support_mode(cls, chat_id: int, enabled: bool):
        """تنظیم حالت پشتیبانی"""
        session = cls.get_support_session(chat_id)
        session["support_mode"] = enabled
        cls.set_support_session(chat_id, session)
    
    @classmethod
    def set_replying_to(cls, chat_id: int, user_id: int):
        """تنظیم اینکه ادمین به کدام کاربر پاسخ می‌دهد"""
        session = cls.get_support_session(chat_id)
        session["replying_to"] = user_id
        cls.set_support_session(chat_id, session)
    
    @classmethod
    def get_replying_to(cls, chat_id: int) -> Optional[int]:
        """دریافت کاربری که ادمین به او پاسخ می‌دهد"""
        session = cls.get_support_session(chat_id)
        return session.get("replying_to")
    
    @classmethod
    def clear_replying_to(cls, chat_id: int):
        """پاک کردن وضعیت پاسخگویی"""
        session = cls.get_support_session(chat_id)
        session.pop("replying_to", None)
        cls.set_support_session(chat_id, session)
    
    @classmethod
    def store_pending_message(cls, user_id: int, message_text: str, message_id: int = None):
        """ذخیره پیام در انتظار پاسخ"""
        session = session_manager.get_user_session(user_id, namespace=cls.PENDING_MESSAGES_NAMESPACE)
        
        # ذخیره پیام با شناسه یکتا
        import time
        timestamp = int(time.time())
        message_key = f"msg_{timestamp}_{message_id}"
        
        session[message_key] = {
            "text": message_text,
            "message_id": message_id,
            "timestamp": timestamp
        }
        
        # محدود کردن تعداد پیام‌های ذخیره شده (حداکثر 50)
        messages = sorted(session.items())
        if len(messages) > 50:
            for key, _ in messages[:-50]:
                del session[key]
        
        session_manager.set_user_session(user_id, session, namespace=cls.PENDING_MESSAGES_NAMESPACE)
        return message_key
    
    @classmethod
    def get_pending_message(cls, user_id: int, message_key: str = None) -> Optional[dict]:
        """دریافت پیام در انتظار پاسخ"""
        session = session_manager.get_user_session(user_id, namespace=cls.PENDING_MESSAGES_NAMESPACE)
        
        if message_key:
            return session.get(message_key)
        
        # برگرداندن آخرین پیام
        messages = [(k, v) for k, v in session.items() if k.startswith("msg_")]
        messages.sort(key=lambda x: x[1].get("timestamp", 0), reverse=True)
        
        if messages:
            return messages[0][1]
        return None
    
    @classmethod
    def delete_pending_message(cls, user_id: int, message_key: str = None):
        """حذف پیام در انتظار پاسخ"""
        session = session_manager.get_user_session(user_id, namespace=cls.PENDING_MESSAGES_NAMESPACE)
        
        if message_key:
            session.pop(message_key, None)
        else:
            # حذف همه پیام‌ها
            keys_to_delete = [k for k in session.keys() if k.startswith("msg_")]
            for key in keys_to_delete:
                del session[key]
        
        session_manager.set_user_session(user_id, session, namespace=cls.PENDING_MESSAGES_NAMESPACE)



###########################################################33


class ForceReply:
    """Force reply markup for Balethon"""
    def __init__(self, selective: bool = False):
        self.force_reply = True
        self.selective = selective
    
    def to_dict(self):
        return {
            "force_reply": self.force_reply,
            "selective": self.selective
        }
    
    def __repr__(self):
        return f"ForceReply(selective={self.selective})"