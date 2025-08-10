# aiobot/webhook.py
import logging
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from aiogram import types
from aiogram.types import Update
from aiogram import Dispatcher

from .dispatcher import dp  # dp: Dispatcher
from .dispatcher import bot  # bot: Bot

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class TelegramBotWebhookView(View):
    async def post(self, request, *args, **kwargs):
        try:
            # دریافت JSON (در Django async view می‌توان از request.body استفاده کرد)
            raw_body = request.body
            # تبدیل به Update با استفاده از Pydantic model_validate (مطابق مستندات)
            update = Update.model_validate_json(raw_body.decode("utf-8"), context={"bot": bot})

            # فرستادن آپدیت به dispatcher (این نسخه از aiogram از feed_update استفاده می‌کند)
            await dp.feed_update(bot, update)

            # برگشت دادن پاسخ به کلاینت (WebHook)
            return JsonResponse({"status": "ok"})

        except Exception as e:
            logger.exception("Webhook error:")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
