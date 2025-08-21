from aiogram import Router, F, types
from aiobot.fc.bot_instance import bot
from aiobot.fc.functions import check_subscription
from aiobot.handlers.start import start_handler

router = Router()


@router.callback_query(F.data == "check_subscription2")
async def check_subscription_handler(callback: types.CallbackQuery):
    # user_id = callback.from_user.id
    #
    # if await check_subscription(bot, user_id):
    #     # ✅ کاربر عضو شده
    #     # await callback.answer("✅ عضویت شما تایید شد.", show_alert=True)
    #
    #     # حالا می‌تونی منو رو نشون بدی یا هندلر اصلی رو کال کنی
    #     await callback.message.edit_text("🎉 خوش اومدی! حالا می‌تونی از امکانات ربات استفاده کنی.")
    #     # یا حتی اینجا redirect کنی به همون start_handler
    #     await start_handler(callback.message)
    # else:
    #     # ❌ کاربر هنوز عضو نشده
    #     await callback.answer(
    #         "❌ هنوز عضو کانال یا گروه نشده‌اید.\nلطفاً اول عضو شوید.",
    #         show_alert=True
    #     )
    user = callback.from_user
    target_chat = int(callback.data.split(":")[1])

    # بررسی مجدد عضویت
    if not await check_subscription(callback.bot, user.id):
        await callback.answer("❌ هنوز عضو نشده‌اید!", show_alert=True)
        return

    # یک Message جعلی با داده‌های کاربر می‌سازیم
    fake_message = types.Message(
        message_id=callback.message.message_id,
        date=callback.message.date,
        chat=callback.message.chat,
        from_user=user,  # 🔥 اینجا کاربر واقعی
        text="/start"
    )

    await start_handler(fake_message)
    await callback.answer("✅ تایید شد!")
