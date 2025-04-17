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


import redis
import json
from collections import OrderedDict

class CartSessionManager:
    def __init__(self, chat_id):
        self.redis = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
        self.chat_id = chat_id

    def set_buttons(self, buttons):
        """ذخیره دکمه‌ها در سشن بدون تبدیل تاپل‌ها به لیست"""
        buttons_list = [(key, tuple(value)) for key, value in buttons.items()]  # اطمینان از حفظ تاپل‌ها
        self.redis.set(f"buttons:{self.chat_id}", json.dumps(buttons_list))  # ذخیره در Redis

    def get_buttons(self):
        """بازیابی دکمه‌های ذخیره‌شده و اطمینان از تبدیل مقدارها به تاپل"""
        buttons = self.redis.get(f"buttons:{self.chat_id}")
        return OrderedDict((key, tuple(value)) for key, value in json.loads(buttons)) if buttons else OrderedDict()

    def clear_buttons(self):
        """پاک کردن دکمه‌های ذخیره‌شده"""
        self.redis.delete(f"buttons:{self.chat_id}")

    def update_buttons(self, new_buttons):
        """بروزرسانی دکمه‌ها بدون حذف کامل آنها"""
        self.clear_buttons()  # پاک کردن دکمه‌های قبلی از سشن
        self.set_buttons(new_buttons)  # ذخیره مقدار جدید




