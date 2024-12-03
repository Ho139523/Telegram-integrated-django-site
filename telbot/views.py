from telebot import TeleBot
from utils.variables.TOKEN import TOKEN

app = TeleBot(token=TOKEN)



@method_decorator(csrf_exempt, name='dispatch')
class TelegramBotWebhookView(View):
    def post(self, request, *args, **kwargs):
        try:
            json_str = request.body.decode('UTF-8')
            logger.info(f"Received data: {json_str}")  # Log the received data
            update = telebot.types.Update.de_json(json.loads(json_str))
            bot.process_new_updates([update])
            return JsonResponse({"status": "success"})
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
            
            
