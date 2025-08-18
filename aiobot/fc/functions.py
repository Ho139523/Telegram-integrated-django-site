# ======================================================= SEND CREATE PROFILE ======================================================= 


# bot_client.py
import time
import hmac
import hashlib
import json
import uuid
import httpx
import asyncio
import traceback
from django.conf import settings

BOT_SECRET = "9cb87c53630243ab6244c20321c00acae9ee896624010ad1b81dd16c89edee91"#settings.BOT_SECRET_KEY
API_URL = "http://127.0.0.1:8000" + "/api/bot/create-profile/"

# Global httpx client
client = httpx.AsyncClient(timeout=5.0)

def sign_payload(secret: str, body_bytes: bytes):
    ts = str(int(time.time()))
    msg = ts.encode() + b"." + body_bytes
    signature = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()
    return ts, signature

async def send_create_profile(tel_id, telegram, fname, lname):
    try:
        payload = {
            "tel_id": tel_id,
            "telegram": telegram,
            "fname": fname,
            "lname": lname
        }

        body_str = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
        body = body_str.encode("utf-8")

        ts, sig = sign_payload(BOT_SECRET, body)
        nonce = str(uuid.uuid4())  # optional

        headers = {
            "X-Bot-Timestamp": ts,
            "X-Bot-Signature": sig,
            "X-Bot-Nonce": nonce,
            "Content-Type": "application/json",
        }

        resp = await client.post(API_URL, headers=headers, content=body)
        return resp  # httpx.Response object

    except Exception as e:
        error_details = traceback.format_exc()
        print(f"⚠️ خطا: {e}\n{error_details}")

if __name__ == "__main__":
    asyncio.run(send_create_profile(1234567890, "helo", "hossein", "mihammadi"))



# ======================================================= SUBSCRIPTION DECORATOR ======================================================= 

import logging
from aiogram import types, Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.variables.CHANNELS import my_channels_with_atsign, my_channels_without_atsign

logger = logging.getLogger(__name__)

# ----------------- Base Functions -----------------
async def check_subscription(bot: Bot, user_id: int, channels=None) -> bool:
    """بررسی عضویت کاربر در کانال‌ها"""
    if channels is None:
        channels = my_channels_with_atsign
    
    for channel in channels:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["kicked", "left"]:
                return False
        except Exception as e:
            logger.error(f"❌ خطا در بررسی عضویت {user_id} در {channel}: {e}")
            return False
    return True


async def subscription_offer(bot: Bot, message: types.Message) -> bool:
    """نمایش دکمه‌ها اگر کاربر عضو نیست"""
    channel_markup = InlineKeyboardMarkup()
    check_button = InlineKeyboardButton(text='✅ عضو شدم', callback_data='check_subscription2')
    channel_subscription_button = InlineKeyboardButton(
        text='📢 در کانال ما عضو شوید',
        url=f"https://t.me/{my_channels_without_atsign[0]}"
    )
    group_subscription_button = InlineKeyboardButton(
        text='💬 در گروه ما عضو شوید',
        url=f"https://t.me/{my_channels_without_atsign[1]}"
    )

    channel_markup.add(channel_subscription_button, group_subscription_button)
    channel_markup.add(check_button)

    if not await check_subscription(bot, message.from_user.id):
        await message.answer(
            "❌ برای تایید عضویت خود در گروه و کانال بر روی دکمه‌ها کلیک کنید.",
            reply_markup=channel_markup
        )
        return False
    return True

# ----------------- Decorator برای تابع‌ها -----------------
def require_subscription(bot: Bot):
    """Decorator برای handlerهای تابعی"""
    def decorator(func):
        async def wrapper(message: types.Message, *args, **kwargs):
            if await subscription_offer(bot, message):
                return await func(message, *args, **kwargs)
        return wrapper
    return decorator