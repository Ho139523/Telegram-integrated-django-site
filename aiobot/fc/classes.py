# ================================================== SEND MENU ==================================================

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



# ================================================== CHECK SUBSCRIPTION ==================================================


import logging
from aiogram import types, Router
from aiogram.filters import BaseFilter
from utils.variables.CHANNELS import my_channels_with_atsign, my_channels_without_atsign
from telbot.menu_sender import send_menu

logger = logging.getLogger(__name__)

class SubscriptionMixin:
    """Mixin برای بررسی عضویت کاربر در کانال‌ها و گروه‌ها"""
    
    my_channels_with_atsign = my_channels_with_atsign
    my_channels_without_atsign = my_channels_without_atsign
    current_site = 'https://intelleum.ir'

    async def check_subscription(self, user_id: int, channels=None) -> bool:
        """✅ بررسی عضویت کاربر در کانال‌ها"""
        if channels is None:
            channels = self.my_channels_with_atsign
        
        for channel in channels:
            try:
                member = await self.bot.get_chat_member(chat_id=channel, user_id=user_id)
                if member.status in ["kicked", "left"]:
                    return False
            except Exception as e:
                logger.error(f" خطا در بررسی عضویت {user_id} در {channel}: {e}")
                return False
        return True

    async def subscription_offer(self, message: types.Message) -> bool:
        """❌ نمایش دکمه‌های عضویت اگر کاربر عضو نیست"""
        channel_markup = types.InlineKeyboardMarkup()
        check_button = types.InlineKeyboardButton(text='✅ عضو شدم', callback_data='check_subscription2')
        channel_subscription_button = types.InlineKeyboardButton(
            text=' در کانال ما عضو شوید',
            url=f"https://t.me/{self.my_channels_without_atsign[0]}"
        )
        group_subscription_button = types.InlineKeyboardButton(
            text=' در گروه ما عضو شوید',
            url=f"https://t.me/{self.my_channels_without_atsign[1]}"
        )

        channel_markup.add(channel_subscription_button, group_subscription_button)
        channel_markup.add(check_button)

        if not await self.check_subscription(user_id=message.from_user.id):
            await message.answer(
                "❌ برای تایید عضویت خود در گروه و کانال بر روی دکمه‌ها کلیک کنید.",
                reply_markup=channel_markup
            )
            return False
        return True

    async def handle_check_subscription(self, call: types.CallbackQuery):
        """✅ هندلر برای دکمه 'عضو شدم'"""
        user_id = call.from_user.id
        chat_id = call.message.chat.id

        if await self.check_subscription(user_id):
            try:
                await call.answer(" در حال بررسی عضویت شما...", show_alert=False)
                await call.message.edit_text(" عضویت شما تایید شد. حالا می‌توانید از امکانات ربات استفاده کنید.")

                profile = ProfileModel.objects.get(tel_id=user_id)
                markup = send_menu(call.message, profile.tel_menu, "main_menu", profile.extra_button_menu)

                await call.message.answer("لطفاً یکی از گزینه‌ها را انتخاب کنید:", reply_markup=markup)
            except Exception as e:
                await call.message.answer(f"خطا در ارسال منو: {e}")
        else:
            await call.answer("❌ شما هنوز در کانال عضو نشده‌اید.", show_alert=True)

    def register_subscription_handler(self, router: Router):
        """ثبت هندلر دکمه عضویت"""
        router.callback_query.register(self.handle_check_subscription, lambda c: c.data == "check_subscription2")


def require_subscription(func):
    async def wrapper(self, message: types.Message, *args, **kwargs):
        if await self.subscription_offer(message):
            return await func(self, message, *args, **kwargs)
    return wrapper