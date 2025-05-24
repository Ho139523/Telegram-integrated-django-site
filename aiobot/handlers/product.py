from aiogram import F
from aiogram.types import Message
from aiogram import Dispatcher

async def admin_panel_handler(message: Message):
    await message.answer("🛠️ پنل مدیریت")

def register_admin_handlers(dp: Dispatcher):
    dp.message.register(admin_panel_handler, F.text == "/admin")
