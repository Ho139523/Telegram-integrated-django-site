# aiobot/handlers/start.py
from aiogram import types, Router
from aiogram.filters import Command
from accounts.models import ProfileModel
import traceback

router = Router()

@router.message(Command("start"))
async def start_handler(message: types.Message):
    try:
        tel_id = message.from_user.id
        tel_username = message.from_user.username or ""
        tel_first_name = message.from_user.first_name or ""
        tel_last_name = message.from_user.last_name or ""

        # بررسی وجود پروفایل به صورت async (Django 4.1+)
        profile_exists = await ProfileModel.objects.filter(tel_id=tel_id).aexists()

        if profile_exists:
            print(f"User with tel_id {tel_id} exists.")
            # اگر خواستی پیام بدی:
            # await message.answer(f"سلام دوباره {tel_first_name}!")
        else:
            print(f"User with tel_id {tel_id} does not exist. Creating new profile.")
            # ایجاد پروفایل به صورت async
            await ProfileModel.objects.acreate(
                tel_id=tel_id,
                telegram=tel_username,
                fname=tel_first_name,
                lname=tel_last_name
            )
            # پیام خوش‌آمدگویی:
            await message.answer(f"🏆 {tel_first_name} عزیز، ثبت نام شما با موفقیت انجام شد.")

        # پیام نهایی برای انتخاب گزینه‌ها
        await message.reply("لطفاً یکی از گزینه‌ها را انتخاب کنید:")

    except Exception as e:
        error_details = traceback.format_exc()
        await message.answer(f"⚠️ خطا: {e}\n{error_details}")
