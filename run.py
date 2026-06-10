# run.py
import asyncio
import sys
from AI.settings import SITE_DOMAIN
import requests

bot = input("[1] Telegram Bot \n[2] Bale Bot\nPlease tell me which one do you want to change? ")



if bot == "1":
    from utils.variables.TOKEN import TOKEN

    BOT_TOKEN = TOKEN
    WEBHOOK_URL = f"{SITE_DOMAIN}/telbot/webhook/"

    try:
        print(f"Webhook URL: {WEBHOOK_URL}")

        # 1) setWebhook
        print("Setting webhook...")

        set_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
        res = requests.post(set_url, json={"url": WEBHOOK_URL}, timeout=20)

        print("SetWebhook Status:", res.status_code)
        print("SetWebhook Response:", res.json())

        # 2) getWebhookInfo
        print("\nChecking webhook info...")

        info_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
        res2 = requests.get(info_url, timeout=20)

        print("GetWebhookInfo Status:", res2.status_code)
        data = res2.json()

        print("Webhook Info:")
        print(data)

        if data.get("ok"):
            info = data["result"]

            print("\n------ WEBHOOK STATUS ------")
            print("URL:", info.get("url"))
            print("Pending updates:", info.get("pending_update_count"))
            print("Last error:", info.get("last_error_message"))
            print("----------------------------")

    except Exception as e:
        print("❌ Error:", e)


elif bot == "2":
    # ================================================
    # 🚀 سخت کدنویسی IP برای دور زدن کامل DNS
    # ================================================
    from utils.variables.TOKEN import BTOKEN as TOKEN
    BOT_TOKEN = TOKEN
    WEBHOOK_URL = f"{SITE_DOMAIN}/balebot/webhook/"
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
