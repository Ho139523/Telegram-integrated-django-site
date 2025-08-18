# start.py
from aiogram import Router, types
from aiogram.filters import Command
import traceback
from aiobot.fc.functions import send_create_profile, require_subscription
from aiobot.fc.classes import MenuSender
from aiobot.fc.bot_instance import bot
from accounts.models import ProfileModel
import httpx



router = Router()
menu_sender = MenuSender(bot)
BASE_URL = "http://127.0.0.1:8000"

def safe_json(resp: httpx.Response) -> dict:
    """تبدیل پاسخ به JSON با مدیریت خطا"""
    try:
        return resp.json()
    except Exception:
        return {"detail": resp.text or "Non-JSON response"}

@router.message(Command("start"))
@require_subscription(bot)
async def start_handler(message: types.Message):
    tel_id = int(message.from_user.id)
    tel_username = message.from_user.username or ""
    tel_first_name = message.from_user.first_name or ""
    tel_last_name = message.from_user.last_name or ""

    try:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            # ایجاد یا بررسی پروفایل
            create_resp = await send_create_profile(
                tel_id, tel_username, tel_first_name, tel_last_name
            )
            create_data = safe_json(create_resp)
            status_code = create_resp.status_code

            # دریافت پروفایل کاربر
            profile_resp = await client.get(f"/api/bot/urd-profile/{tel_id}/")
            profile = safe_json(profile_resp)

        # ساخت متن و ارسال منو بر اساس وضعیت ثبت‌نام
        if status_code == 200 and create_data.get("created") is True:
            text = f"🎉 {tel_first_name} عزیز، ثبت‌نامت با موفقیت انجام شد."
        elif status_code == 409:
            text = f"{tel_first_name} عزیز، شما قبلاً در ربات ثبت‌نام کرده‌اید."
        elif status_code == 400:
            return await message.answer(
                f"⚠️ داده‌های ارسالی نامعتبر است: {create_data.get('details') or create_data.get('detail')}"
            )
        else:
            return await message.answer(
                f"⚠️ خطای سرور ({status_code}): {create_data.get('detail', 'مشکلی پیش آمد')}"
            )

        # ارسال منو به کاربر
        await menu_sender.send_menu(
            user_id=message.chat.id,
            text=text,
            options=profile.get('tel_menu', []),
            extra_buttons=["⚙️ تنظیمات"],
            current_menu="main_menu",
            keyboard_type="reply"
        )

    except Exception as e:
        error_details = traceback.format_exc()
        await message.answer(f"⚠️ خطا در اجرای دستور /start:\n{e}\n{error_details}")
