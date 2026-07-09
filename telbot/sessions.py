############################################## SEE PRODUCTS, CATEGORY MENU, Home, Back to Previous Menu, 10 products ##############################################

import redis
import json

import redis
import json
from django.conf import settings

class SessionManager:
    
    from django.conf import settings

    redis_url = getattr(settings, "REDIS_URL", "redis://127.0.0.1:6379/0")

    DEFAULT_TTL = 60 * 60 * 6  # 6 hours

    def __init__(self, redis_url=None):
        self.redis_client = redis.StrictRedis.from_url(
            redis_url or settings.REDIS_URL,
            decode_responses=True
        )

    def _make_key(self, user_id, namespace="default"):
        return f"telbot:{namespace}:{user_id}"

    # ------------------
    # New Clean Methods
    # ------------------

    def get(self, user_id, namespace="default"):
        key = self._make_key(user_id, namespace)
        data = self.redis_client.get(key)
        return json.loads(data) if data else {}

    def set(self, user_id, session_data, namespace="default", ttl=None):
        key = self._make_key(user_id, namespace)
        self.redis_client.set(
            key,
            json.dumps(session_data),
            ex=ttl or self.DEFAULT_TTL
        )

    def update(self, user_id, new_data, namespace="default", ttl=None):
        key = self._make_key(user_id, namespace)

        with self.redis_client.pipeline() as pipe:
            while True:
                try:
                    pipe.watch(key)
                    current = pipe.get(key)
                    current_data = json.loads(current) if current else {}
                    current_data.update(new_data)

                    pipe.multi()
                    pipe.set(
                        key,
                        json.dumps(current_data),
                        ex=ttl or self.DEFAULT_TTL
                    )
                    pipe.execute()
                    break
                except redis.WatchError:
                    continue

    def delete(self, user_id, namespace="default"):
        key = self._make_key(user_id, namespace)
        self.redis_client.delete(key)

    # ------------------
    # Backward Compatibility Layer
    # ------------------

    def get_user_session(self, user_id, namespace="default"):
        return self.get(user_id, namespace)

    def set_user_session(self, user_id, session_data, namespace="default"):
        self.set(user_id, session_data, namespace)

    def update_user_session(self, user_id, new_data, namespace="default"):
        self.update(user_id, new_data, namespace)

    def reset_user_session(self, user_id, namespace="default"):
        self.delete(user_id, namespace)

    def lock(self, user_id, operation, namespace="menu"):
        session = self.get(user_id, namespace)
        session["lock"] = operation
        self.set(user_id, session, namespace)

    def unlock(self, user_id, namespace="menu"):
        session = self.get(user_id, namespace)
        session.pop("lock", None)
        self.set(user_id, session, namespace)

    def is_locked(self, user_id, namespace="menu"):
        session = self.get(user_id, namespace)
        return session.get("lock")

    def can_execute(self, user_id, operation=None, namespace="menu"):
        """
        اگر قفلی وجود نداشته باشد True
        اگر operation مشخص شده باشد فقط همان عملیات اجازه ادامه دارد.
        """
        lock = self.is_locked(user_id, namespace)

        if lock is None:
            return True

        if operation is not None:
            return lock == operation

        return False


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

############################################## PRODUCT LIST ##############################################

import zlib

class RedisExportManager:
    """مدیریت کش و سشن‌های مربوط به صادرات با Redis"""
    
    def __init__(self, redis_url="redis://localhost:6379/0"):
        self.redis_client = redis.StrictRedis.from_url(redis_url, decode_responses=False)
        self.export_cache_time = 3600
        self.session_namespace = "product_export"
    
    def _make_export_key(self, store_id, data_type="full"):
        return f"export:{self.session_namespace}:{store_id}:{data_type}"
    
    def _make_session_key(self, user_id):
        return f"session:{self.session_namespace}:{user_id}"
    
    def _compress_data(self, data):
        """فشرده‌سازی داده برای ذخیره در Redis"""
        # جدا کردن file_data و تبدیل آن به base64
        file_data = data.pop('file_data')
        file_data_base64 = base64.b64encode(file_data).decode('utf-8')
        
        # فشرده‌سازی metadata
        data['file_data_base64'] = file_data_base64
        compressed_data = zlib.compress(json.dumps(data, default=str).encode('utf-8'))
        
        return compressed_data
    
    def _decompress_data(self, compressed_data):
        """بازیابی داده فشرده از Redis"""
        try:
            # decompress داده‌ها
            decompressed = zlib.decompress(compressed_data).decode('utf-8')
            data = json.loads(decompressed)
            
            # تبدیل file_data از base64 به بایت
            if 'file_data_base64' in data:
                file_data = base64.b64decode(data['file_data_base64'])
                data['file_data'] = file_data
                del data['file_data_base64']
            
            return data
        except (zlib.error, json.JSONDecodeError, KeyError, base64.binascii.Error) as e:
            print(f"Decompression error: {e}")
            return None
    
    def get_cached_export(self, store_id):
        """دریافت داده صادرات از کش"""
        cache_key = self._make_export_key(store_id)
        cached = self.redis_client.get(cache_key)
        if cached:
            return self._decompress_data(cached)
        return None
    
    def cache_export(self, store_id, data):
        """ذخیره داده صادرات در کش"""
        cache_key = self._make_export_key(store_id)
        
        # اطمینان از اینکه file_data به صورت بایت است
        if not isinstance(data['file_data'], bytes):
            data['file_data'] = data['file_data'].encode('utf-8')
        
        compressed = self._compress_data(data)
        self.redis_client.setex(cache_key, self.export_cache_time, compressed)
    
    def get_user_session(self, user_id):
        """دریافت سشن کاربر"""
        session_key = self._make_session_key(user_id)
        session_data = self.redis_client.get(session_key)
        return json.loads(session_data) if session_data else {}
    
    def set_user_session(self, user_id, session_data):
        """ذخیره سشن کاربر"""
        session_key = self._make_session_key(user_id)
        self.redis_client.setex(session_key, 7200, json.dumps(session_data))
    
    def update_user_session(self, user_id, new_data):
        """بروزرسانی سشن کاربر"""
        session = self.get_user_session(user_id)
        session.update(new_data)
        self.set_user_session(user_id, session)
    
    def reset_user_session(self, user_id):
        """پاک کردن سشن کاربر"""
        session_key = self._make_session_key(user_id)
        self.redis_client.delete(session_key)



session_manager = SessionManager()