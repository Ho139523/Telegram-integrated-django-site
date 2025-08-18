from aiogram import types
import json
import redis
from telbot.sessions import SessionManager


class MenuSender:
    def __init__(self, bot):
        self.bot = bot
        self.session_manager = SessionManager()

    async def send_menu(
        self,
        user_id: int,
        text: str,
        options: list,
        current_menu: str,
        extra_buttons: list = None,
        keyboard_type: str = "reply"
    ):
        """
        ارسال منو به کاربر و ذخیره نام منو در session

        :param user_id: آیدی کاربر
        :param text: متن پیام
        :param options: لیست گزینه‌ها
        :param current_menu: نام منو برای ذخیره در session
        :param extra_buttons: دکمه‌های اضافی (اختیاری)
        :param keyboard_type: "reply" یا "inline"
        """

        if keyboard_type == "reply":
            # ساخت ReplyKeyboardMarkup با keyboard خالی
            markup = types.ReplyKeyboardMarkup(
                keyboard=[],
                resize_keyboard=True
            )

            # افزودن دکمه‌های اصلی
            for row in [options[i:i+3] for i in range(0, len(options), 3)]:
                markup.keyboard.append(
                    [types.KeyboardButton(text=opt) for opt in row]
                )

            # افزودن دکمه‌های اضافه
            if extra_buttons:
                for row in [extra_buttons[i:i+2] for i in range(0, len(extra_buttons), 2)]:
                    markup.keyboard.append(
                        [types.KeyboardButton(text=opt) for opt in row]
                    )

        elif keyboard_type == "inline":
            # ساخت InlineKeyboardMarkup با inline_keyboard خالی
            markup = types.InlineKeyboardMarkup(
                inline_keyboard=[]
            )

            # افزودن دکمه‌های اصلی
            for row in [options[i:i+3] for i in range(0, len(options), 3)]:
                markup.inline_keyboard.append(
                    [types.InlineKeyboardButton(text=opt, callback_data=opt) for opt in row]
                )

            # افزودن دکمه‌های اضافه
            if extra_buttons:
                for row in [extra_buttons[i:i+2] for i in range(0, len(extra_buttons), 2)]:
                    markup.inline_keyboard.append(
                        [types.InlineKeyboardButton(text=opt, callback_data=opt) for opt in row]
                    )
        else:
            raise ValueError("keyboard_type باید 'reply' یا 'inline' باشد")

        # ذخیره نام منو در session
        self.session_manager.update_user_session(
            user_id, {"current_menu": current_menu}
        )

        # ارسال پیام
        await self.bot.send_message(user_id, text, reply_markup=markup)

