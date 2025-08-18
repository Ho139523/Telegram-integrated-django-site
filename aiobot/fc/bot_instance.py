# aiobot/bot_instance.py
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from utils.variables.TOKEN import TOKEN

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
