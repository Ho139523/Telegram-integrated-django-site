from django.utils import timezone
from django.core.exceptions import PermissionDenied
from products.models import Store
from subscription.models import Plan, Subscription
from subscription.models import SubscriptionUsage  # مسیر را طبق پروژه خودت تنظیم کن
from accounts.models import ProfileModel
from utils.variables.TOKEN import TOKEN
import telebot
import traceback

app = telebot.TeleBot(
    TOKEN,
    threaded=True,
    num_threads=5
)


class SubscriptionRequiredMixin:
    """
    Mixin حرفه‌ای برای بررسی Subscription
    پشتیبانی از:
    - Feature check
    - Usage limit
    - Trial limit
    - Auto downgrade
    - CallbackQuery alert
    """

    feature_code: str = None
    auto_increment_usage: bool = True  # اگر نخواستی خودکار usage افزایش یابد False کن

    # ---------------------------------------
    # Helpers
    # ---------------------------------------

    def _get_chat_id(self, update):
        if hasattr(update, "chat"):
            return update.chat.id, False  # Message
        elif hasattr(update, "message"):
            return update.message.chat.id, True  # Callback
        elif hasattr(update, "from_user"):
            return update.from_user.id, False
        else:
            raise Exception("Cannot detect update type")

    def _send_message(self, update, text, is_callback=False):
        try:
            chat_id, _ = self._get_chat_id(update)

            if is_callback:
                app.answer_callback_query(
                    update.id,
                    text,
                    show_alert=True
                )
            else:
                app.send_message(chat_id, text)
        except Exception:
            print(traceback.format_exc())

    def _get_subscription(self, chat_id):
        profile = ProfileModel.objects.get(tel_id=chat_id)
        store = Store.objects.select_related("subscription").filter(owner=profile).first()

        if not store:
            return None

        return getattr(store, "subscription", None)

    # ---------------------------------------
    # Core Logic
    # ---------------------------------------

    def _lazy_expire(self, sub):
        if sub.status in ["trial", "active"] and sub.end_date <= timezone.now():
            sub.status = "expired"
            sub.save(update_fields=["status"])
            self._auto_downgrade(sub)

    def _auto_downgrade(self, sub):
        """
        وقتی سابسکریپشن expire شد
        پلن را به basic تغییر می‌دهد
        """
        basic_plan = Plan.objects.filter(code="basic").first()
        if basic_plan and sub.plan != basic_plan:
            sub.plan = basic_plan
            sub.save(update_fields=["plan"])

    def _check_feature(self, sub, update, is_callback):
        if not self.feature_code:
            return None

        relation = sub.plan.features.filter(
            feature__code=self.feature_code
        ).select_related("feature").first()

        if not relation:
            self._send_message(
                update,
                "❌ این قابلیت در پلن شما فعال نیست.",
                is_callback
            )
            raise PermissionDenied("Feature not allowed")

        return relation

    def _check_usage_limit(self, sub, relation, update, is_callback):
        if not relation:
            return

        limit = int(relation.value or 0)

        usage, _ = SubscriptionUsage.objects.get_or_create(
            subscription=sub,
            feature=relation.feature
        )

        if limit > 0 and usage.used_count >= limit:
            self._send_message(
                update,
                "❌ محدودیت استفاده از این قابلیت به پایان رسیده است.",
                is_callback
            )
            raise PermissionDenied("Usage limit reached")

        if self.auto_increment_usage:
            usage.used_count += 1
            usage.save(update_fields=["used_count"])

    def _check_trial(self, sub, update, is_callback):
        if sub.status == "trial":
            if sub.end_date <= timezone.now():
                self._send_message(
                    update,
                    "❌ دوره آزمایشی شما به پایان رسیده است.",
                    is_callback
                )
                raise PermissionDenied("Trial expired")

    # ---------------------------------------
    # Main Entry
    # ---------------------------------------

    def check_subscription(self, update):
        """
        این متد را قبل از اجرای handler صدا بزن
        """
        chat_id, is_callback = self._get_chat_id(update)

        sub = self._get_subscription(chat_id)

        if not sub:
            self._send_message(
                update,
                "❌ شما اشتراکی ندارید. لطفاً اشتراک تهیه کنید.",
                is_callback
            )
            raise PermissionDenied("No subscription")

        # Lazy expire
        self._lazy_expire(sub)

        # وضعیت معتبر؟
        if sub.status not in ["trial", "active"]:
            self._send_message(
                update,
                "❌ اشتراک شما منقضی شده است.",
                is_callback
            )
            raise PermissionDenied("Subscription expired")

        # Trial check
        self._check_trial(sub, update, is_callback)

        # Feature check
        relation = self._check_feature(sub, update, is_callback)

        # Usage check
        self._check_usage_limit(sub, relation, update, is_callback)

        return True




# Usage example:

# class Promote(SubscriptionRequiredMixin):

# def _show_offer(self, update=None):
        # اول سابسکریپشن چک شود
        # self.check_subscription(update)
        # سپس ادامه عملیات