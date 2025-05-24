import logging
from utils.variables.CHANNELS import my_channels_with_atsign, my_channels_without_atsign

logger = logging.getLogger(__name__)

class SubscriptionClass:
	def __init__(self, bot: TeleBot):
		self.bot = bot
		self.my_channels_with_atsign = my_channels_with_atsign
		self.my_channels_without_atsign = my_channels_without_atsign
		self.current_site = 'https://intelleum.ir'
		
	def handle_check_subscription(self, call: types.CallbackQuery):
		"""✅ بررسی عضویت هنگام کلیک روی دکمه 'عضو شدم'"""
		chat_id = call.message.chat.id
		user_id = call.from_user.id

		

		# بررسی عضویت
		is_member = self.check_subscription(user_id)  

		if is_member:
			
			try:
			
				# ✅ پاسخ اولیه به Callback Query
				await call.answer("🔄 در حال بررسی عضویت شما...", show_alert=False)

				await call.message.edit_text(
					"🎉 عضویت شما تایید شد. حالا می‌توانید از امکانات ربات استفاده کنید."
				)


				profile = ProfileModel.objects.get(tel_id=user_id)
				main_menu = profile.tel_menu
				extra_buttons = profile.extra_button_menu
				markup = send_menu(call.message, main_menu, "main_menu", extra_buttons)

				await self.bot.send_message(user_id, "لطفاً یکی از گزینه‌ها را انتخاب کنید:", reply_markup=markup)
			except Exception as e:
				await self.bot.send_message(user_id, f"error iis: {e}")
		else:
			await call.answer(call.id, "❌ شما هنوز در کانال عضو نشده‌اید.", show_alert=True)

	def register_handlers(self):
		"""🔹 ثبت هندلرهای مورد نیاز"""
		self.bot.callback_query_handler(func=lambda call: call.data == "check_subscription2")(self.handle_check_subscription)

	def check_subscription(self, user, channels=None):
		"""✅ بررسی می‌کند که کاربر در کانال عضو شده است یا نه"""
		if channels is None:
			channels = self.my_channels_with_atsign
		for channel in channels:
			try:
				is_member = await self.bot.get_chat_member(chat_id=channel, user_id=user)
				if is_member.status in ["kicked", "left"]:
					return False
			except Exception as e:
				logger.error(f"🚨 خطا در بررسی عضویت کاربر {user} در کانال {channel}: {e}")
				return False
		return True
		
	def subscription_offer(self, message):
		"""❌ اگر کاربر عضو نباشد، دکمه‌های عضویت نمایش داده شوند"""
		channel_markup = types.InlineKeyboardMarkup()
		check_subscription_button = types.InlineKeyboardButton(text='✅ عضو شدم', callback_data='check_subscription2')
		channel_subscription_button = types.InlineKeyboardButton(text='📢 در کانال ما عضو شوید', url=f"https://t.me/{self.my_channels_without_atsign[0]}")
		group_subscription_button = types.InlineKeyboardButton(text="💬 در گروه ما عضو شوید", url=f"https://t.me/{self.my_channels_without_atsign[1]}")

		channel_markup.add(channel_subscription_button, group_subscription_button)
		channel_markup.add(check_subscription_button)

		if not self.check_subscription(user=message.from_user.id):
			self.bot.send_message(message.chat.id, "❌ برای تایید عضویت خود در گروه و کانال بر روی دکمه‌ها کلیک کنید.", reply_markup=channel_markup)
			return False
		return True