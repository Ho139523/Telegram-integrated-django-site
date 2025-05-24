from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from utils.variables.TOKEN import TOKEN
from .handlers import register_all_handlers

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ثبت همهی هندلرها
register_all_handlers(dp)
