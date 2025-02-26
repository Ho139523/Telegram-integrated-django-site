from collections import defaultdict

class SessionManager:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._instance.user_sessions = defaultdict(lambda: {"current_menu": None})
        return cls._instance

    def reset_user_session(self, user_id):
        """Reset a specific user's session."""
        if user_id in self.user_sessions:
            self.user_sessions[user_id] = {"current_menu": None}

# ایجاد نمونه Singleton
session_manager = SessionManager()


import json
import redis
from collections import OrderedDict

class CartSessionManager:
    def __init__(self, chat_id):
        self.redis = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
        self.chat_id = chat_id

    def set_buttons(self, buttons):
        """ذخیره دکمه‌ها در سشن به‌صورت لیست مرتب‌شده"""
        buttons_list = list(buttons.items())  # تبدیل OrderedDict به لیست از تاپل‌ها
        self.redis.set(f"buttons:{self.chat_id}", json.dumps(buttons_list))  # ذخیره در Redis

    def get_buttons(self):
        """بازیابی دکمه‌های ذخیره‌شده و تبدیل به OrderedDict"""
        buttons = self.redis.get(f"buttons:{self.chat_id}")
        return OrderedDict(json.loads(buttons)) if buttons else OrderedDict()  # بازسازی OrderedDict

    def clear_buttons(self):
        """پاک کردن دکمه‌های ذخیره‌شده"""
        self.redis.delete(f"buttons:{self.chat_id}")

    def update_buttons(self, new_buttons):
        """بروزرسانی دکمه‌ها بدون حذف کامل آنها"""
        current_buttons = self.get_buttons()  # دکمه‌های فعلی را دریافت کن
        if current_buttons != new_buttons:  # فقط در صورتی که تغییر کنند، ذخیره شود
            self.set_buttons(new_buttons)


