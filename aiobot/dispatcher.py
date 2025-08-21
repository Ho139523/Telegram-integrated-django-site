# aiobot/dispatcher.py
import redis.asyncio as redis
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.client.default import DefaultBotProperties

from utils.variables.TOKEN import TOKEN
from .handlers import register_all_handlers

# اتصال به Redis
# اگر Redis روی سرور دیگه باشه، host و port رو تغییر بده
redis_client = redis.Redis(
    host="localhost",   # یا آدرس IP سرور Redis
    port=6379,
    db=0
)

# ساخت storage بر پایه Redis
storage = RedisStorage(redis=redis_client)

# ساخت Bot
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))

# ساخت Dispatcher با RedisStorage
dp = Dispatcher(storage=storage)

# ثبت همه‌ی Routerها و هندلرها
register_all_handlers(dp)
