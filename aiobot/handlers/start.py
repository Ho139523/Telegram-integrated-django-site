from aiogram import types
from aiogram import Router
from aiogram.filters import Command
from aiogram.utils.markdown import hbold
import requests
import traceback

from accounts.models import ProfileModel
# from ... import subscription  # فرض می‌کنیم ماژول subscription هم هست
# from ...menu import send_menu  # تابعی که منو می‌سازه

router = Router()

@router.message(Command("start"))
async def start_handler(message: types.Message):
    try:
        tel_id = message.from_user.id
        tel_username = message.from_user.username 
        tel_first_name = message.from_user.first_name
        tel_last_name = message.from_user.last_name

        current_site = "https://intelium.ir"  # یا از settings بگیر
        profile_exists = ProfileModel.objects.filter(tel_id=tel_id).exists()
            
        if profile_exists:
            print(f"User with tel_id {tel_id} exists.")
        
        else:
            print(f"User with tel_id {tel_id} does not exist. Creating a new entry.")
            
        print(tel_last_name)
    #     if response.status_code == 201:
    #         await message.answer(
    #             f"🏆 {tel_first_name} عزیز ثبت نامت با موفقیت انجام شد.\n\n"
    #         )
    #     else:
    #         await message.answer(
    #             f"{tel_first_name} عزیز شما قبلا در ربات ثبت نام کرده‌اید."
    #         )

    #     profile, created = ProfileModel.objects.get_or_create(
    #         tel_id=tel_id,
    #         defaults={"telegram": tel_username, "fname": tel_first_name, "lname": tel_last_name}
    #     )

    #     if created:
    #         print("پروفایل جدید ساخته شد")

    #     # if subscription.subscription_offer(message):
    #     #     main_menu = profile.tel_menu
    #     #     extra_buttons = profile.extra_button_menu
    #     #     markup = send_menu(message, main_menu, "main_menu", extra_buttons)
    #     await message.answer("لطفاً یکی از گزینه‌ها را انتخاب کنید:")#, reply_markup=markup)

    except Exception as e:
        error_details = traceback.format_exc()
        await message.answer(f"⚠️ خطا: {e}\n{error_details}")
