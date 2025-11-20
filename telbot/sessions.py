############################################## SEE PRODUCTS, CATEGORY MENU, Home, Back to Previous Menu, 10 products ##############################################

import redis
import json

class SessionManager:
    def __init__(self, redis_url="redis://localhost:6379/0"):
        self.redis_client = redis.StrictRedis.from_url(redis_url)

    def _make_key(self, user_id, namespace="default"):
        return f"user_session:{namespace}:{user_id}"

    def get_user_session(self, user_id, namespace="default"):
        key = self._make_key(user_id, namespace)
        session_data = self.redis_client.get(key)
        return json.loads(session_data) if session_data else {}

    def set_user_session(self, user_id, session_data, namespace="default"):
        key = self._make_key(user_id, namespace)
        self.redis_client.set(key, json.dumps(session_data))

    def update_user_session(self, user_id, new_data, namespace="default"):
        """Safely merge into existing session data."""
        session = self.get_user_session(user_id, namespace)
        session.update(new_data)
        self.set_user_session(user_id, session, namespace)

    def reset_user_session(self, user_id, namespace="default"):
        key = self._make_key(user_id, namespace)
        self.redis_client.delete(key)


############################################## SEND CART ##############################################


import redis
import json
from collections import OrderedDict

class CartSessionManager:
    def __init__(self, chat_id):
        self.redis = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
        self.chat_id = chat_id

    def set_buttons(self, buttons):
        """ذخیره دکمه‌ها در سشن به فرمت لیست جدید"""
        # buttons باید لیستی از تاپل‌های (text, callback_data, index) باشد
        self.redis.set(f"buttons:{self.chat_id}", json.dumps(buttons))

    def get_buttons(self):
        """بازیابی دکمه‌های ذخیره‌شده به فرمت لیست"""
        buttons = self.redis.get(f"buttons:{self.chat_id}")
        return json.loads(buttons) if buttons else []

    def clear_buttons(self):
        """پاک کردن دکمه‌های ذخیره‌شده"""
        self.redis.delete(f"buttons:{self.chat_id}")

    def update_buttons(self, new_buttons):
        """بروزرسانی دکمه‌ها"""
        self.set_buttons(new_buttons)


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




session_manager = SessionManager()