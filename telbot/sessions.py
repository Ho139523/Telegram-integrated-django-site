############################################## SEE PRODUCTS, CATEGORY MENU, Home, Back to Previous Menu, 10 products ##############################################

import redis
import json

class SessionManager:
    def __init__(self, host='localhost', port=6379, db=0):
        self.redis_client = redis.StrictRedis(host=host, port=port, db=db, decode_responses=True)

    def get_user_session(self, user_id):
        """بازیابی اطلاعات جلسه کاربر از Redis"""
        session_data = self.redis_client.get(f"user_session:{user_id}")
        return json.loads(session_data) if session_data else {"current_menu": None}

    def set_user_session(self, user_id, session_data):
        """ذخیره اطلاعات جلسه کاربر در Redis"""
        self.redis_client.set(f"user_session:{user_id}", json.dumps(session_data))

    def reset_user_session(self, user_id):
        """حذف جلسه کاربر از Redis"""
        self.redis_client.delete(f"user_session:{user_id}")


############################################## SEND CART ##############################################


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


############################################## ADD PRODUCT ##############################################

import redis
import json

class RedisStateManager:
    def __init__(self, chat_id):
        self.redis = redis.StrictRedis(host='localhost', port=6379, db=1, decode_responses=True)
        self.chat_id = chat_id
        self.prefix = f"user_data:{chat_id}"

    def set_state(self, state):
        self.redis.hset(self.prefix, "state", state)

    def get_state(self):
        return self.redis.hget(self.prefix, "state")

    def save_user_data(self, key, value):
        self.redis.hset(self.prefix, key, json.dumps(value))

    def get_user_data(self, key):
        value = self.redis.hget(self.prefix, key)
        return json.loads(value) if value else None

    def get_all_user_data(self):
        data = self.redis.hgetall(self.prefix)
        return {k: json.loads(v) for k, v in data.items()}

    def delete_state(self):
        self.redis.delete(self.prefix)




