# run.py
import asyncio
import sys
from utils.variables.TOKEN import BTOKEN as TOKEN
from AI.settings import current_site
import aiohttp

bot = input("[1] Telegram Bot \n[2] Bale Bot\nPlease tell me which one do you want to change? ")

if bot == "1":
    # ... (کد مربوط به تلگرام) ...
    pass
elif bot == "2":
    # ================================================
    # 🚀 سخت کدنویسی IP برای دور زدن کامل DNS
    # ================================================
    BOT_TOKEN = TOKEN
    WEBHOOK_URL = f"{current_site}/balebot/webhook/"
    BOT_API_IP = "2.189.68.126"  # IP اصلی tapi.bale.ai که پیدا کردی

    # ساخت URL با IP به جای نام دامنه
    # هدر `Host: tapi.bale.ai` را اضافه می‌کنیم تا سرور IP را بپذیرد
    webhook_url = f"https://{BOT_API_IP}/bot{BOT_TOKEN}/setWebhook"
    params = {"url": WEBHOOK_URL}
    headers = {"Host": "tapi.bale.ai"}  # 🔑 کلید اصلی

    async def setup_bale_webhook():
        connector = aiohttp.TCPConnector()
        async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
            try:
                async with session.get(webhook_url, params=params, ssl=False) as response:
                    # ssl=False فقط برای تست
                    print(f"Status: {response.status}")
                    try:
                        json_response = await response.json()
                        print(f"✅ Result: {json_response}")
                    except:
                        text = await response.text()
                        print(f"⚠️ Response (not JSON): {text[:200]}")
            except Exception as e:
                print(f"❌ Error: {e}")

    print(f"Webhook URL: {WEBHOOK_URL}")
    print(f"Sending request to IP: {BOT_API_IP}...")
    asyncio.run(setup_bale_webhook())

else:
    print("Your choice is out of range!")
    sys.exit()
