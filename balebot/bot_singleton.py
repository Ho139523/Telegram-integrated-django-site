from balethon import Client
import asyncio
from utils.variables.TOKEN import BTOKEN

_bot = None
_init_lock = asyncio.Lock()


async def get_bot():
    global _bot

    if _bot is not None:
        return _bot

    async with _init_lock:
        if _bot is None:
            _bot = Client(BTOKEN)

            await _bot.initialize()
            await _bot.connect()   # ✅ فقط این

            print("✅ Bot fully initialized")

    return _bot