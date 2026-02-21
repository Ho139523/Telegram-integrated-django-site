from functools import wraps
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from products.models import Store
from accounts.models import ProfileModel
from subscription.models import Subscription
import traceback


import telebot
from utils.variables.TOKEN import TOKEN

app = telebot.TeleBot(
    TOKEN,
    threaded=True,
    num_threads=5
)

def subscription_required(feature_code=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            update = args[0]  # فرض بر این است که اولین آرگومان آپدیت است

            try:
                # تشخیص نوع آپدیت
                if hasattr(update, "chat"):  
                    # Message
                    chat_id = update.chat.id
                    is_callback = False
                else:
                    # CallbackQuery
                    chat_id = update.message.chat.id
                    is_callback = True

                profile = ProfileModel.objects.get(tel_id=chat_id)
                store = Store.objects.filter(owner=profile).first()

                if not store:
                    return

                sub = Subscription.objects.filter(store=store).first()

                if not sub:
                    bot = app

                    if is_callback:
                        bot.answer_callback_query(
                            update.id,
                            "❌ شما اشتراکی ندارید. لطفاً برای استفاده از این ویژگی اشتراک تهیه کنید.",
                            show_alert=True
                        )
                    else:
                        bot.send_message(
                            chat_id,
                            "❌ شما اشتراکی ندارید. لطفاً برای استفاده از این ویژگی اشتراک تهیه کنید."
                        )

                    return

                # Lazy Expire
                if sub.status in ['trial', 'active'] and sub.end_date <= timezone.now():
                    sub.status = 'expired'
                    sub.save(update_fields=['status'])

                if sub.status not in ['trial', 'active']:

                    bot = app

                    if is_callback:
                        bot.answer_callback_query(
                            update.id,
                            "❌ اشتراک شما منقضی شده است.",
                            show_alert=True
                        )
                    else:
                        bot.send_message(
                            chat_id,
                            "❌ اشتراک شما منقضی شده است."
                        )

                    return

                return func(*args, **kwargs)

            except Exception:
                print(traceback.format_exc())
                return

        return wrapper
    return decorator
