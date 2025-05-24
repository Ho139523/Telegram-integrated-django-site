import json
import logging
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from aiogram import types

from .dispatcher import dp, bot

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class TelegramBotWebhookView(View):
    async def post(self, request):
        try:
            raw_data = request.body
            update = types.Update(**json.loads(raw_data.decode("utf-8")))
            await dp.feed_webhook_update(bot, update)
            return JsonResponse({"status": "ok"})
        except Exception as e:
            logger.exception("Webhook error:")
            return JsonResponse({"status": "error", "message": str(e)})
