# utils/balebot/ClassBase.py
import traceback
from typing import Dict, Optional
from balethon.objects import Message, CallbackQuery
from utils.balebot.decorators import store_messages, clear_previous_messages, clear_messages_on_command, auto_clear
from utils.balebot.helpers import t, get_profile
from telbot.sessions import session_manager
from utils.balebot.handlers import home_handler
from balethon import objects
import os
from utils.telbot.functions import add_performance_monitoring_to_class
from utils.balebot.helpers import SendMarkup
from django.core.exceptions import ValidationError

# ================================================
# کلاس مدیریت چت پشتیبانی
# ================================================

class SupportChatManager:
    """مدیریت چت‌های پشتیبانی"""
    
    SUPPORT_NAMESPACE = "support_chat"
    PENDING_MESSAGES_NAMESPACE = "pending_messages"
    
    @classmethod
    def get_support_session(cls, chat_id: int) -> dict:
        """دریافت سشن پشتیبانی کاربر"""
        return session_manager.get_user_session(chat_id, namespace=cls.SUPPORT_NAMESPACE)
    
    @classmethod
    def set_support_session(cls, chat_id: int, session: dict):
        """ذخیره سشن پشتیبانی کاربر"""
        session_manager.set_user_session(chat_id, session, namespace=cls.SUPPORT_NAMESPACE)
    
    @classmethod
    def clear_support_session(cls, chat_id: int):
        """پاک کردن سشن پشتیبانی کاربر"""
        session_manager.delete(chat_id, namespace=cls.SUPPORT_NAMESPACE)
    
    @classmethod
    def is_support_mode(cls, chat_id: int) -> bool:
        """بررسی اینکه کاربر در حالت پشتیبانی است"""
        session = cls.get_support_session(chat_id)
        return session.get("support_mode", False)
    
    @classmethod
    def set_support_mode(cls, chat_id: int, enabled: bool):
        """تنظیم حالت پشتیبانی"""
        session = cls.get_support_session(chat_id)
        session["support_mode"] = enabled
        cls.set_support_session(chat_id, session)
    
    @classmethod
    def set_replying_to(cls, chat_id: int, user_id: int):
        """تنظیم اینکه ادمین به کدام کاربر پاسخ می‌دهد"""
        session = cls.get_support_session(chat_id)
        session["replying_to"] = user_id
        cls.set_support_session(chat_id, session)
    
    @classmethod
    def get_replying_to(cls, chat_id: int) -> Optional[int]:
        """دریافت کاربری که ادمین به او پاسخ می‌دهد"""
        session = cls.get_support_session(chat_id)
        return session.get("replying_to")
    
    @classmethod
    def clear_replying_to(cls, chat_id: int):
        """پاک کردن وضعیت پاسخگویی"""
        session = cls.get_support_session(chat_id)
        session.pop("replying_to", None)
        cls.set_support_session(chat_id, session)
    
    @classmethod
    def store_pending_message(cls, user_id: int, message_text: str, message_id: int = None):
        """ذخیره پیام در انتظار پاسخ"""
        session = session_manager.get_user_session(user_id, namespace=cls.PENDING_MESSAGES_NAMESPACE)
        
        # ذخیره پیام با شناسه یکتا
        import time
        timestamp = int(time.time())
        message_key = f"msg_{timestamp}_{message_id}"
        
        session[message_key] = {
            "text": message_text,
            "message_id": message_id,
            "timestamp": timestamp
        }
        
        # محدود کردن تعداد پیام‌های ذخیره شده (حداکثر 50)
        messages = sorted(session.items())
        if len(messages) > 50:
            for key, _ in messages[:-50]:
                del session[key]
        
        session_manager.set_user_session(user_id, session, namespace=cls.PENDING_MESSAGES_NAMESPACE)
        return message_key
    
    @classmethod
    def get_pending_message(cls, user_id: int, message_key: str = None) -> Optional[dict]:
        """دریافت پیام در انتظار پاسخ"""
        session = session_manager.get_user_session(user_id, namespace=cls.PENDING_MESSAGES_NAMESPACE)
        
        if message_key:
            return session.get(message_key)
        
        # برگرداندن آخرین پیام
        messages = [(k, v) for k, v in session.items() if k.startswith("msg_")]
        messages.sort(key=lambda x: x[1].get("timestamp", 0), reverse=True)
        
        if messages:
            return messages[0][1]
        return None
    
    @classmethod
    def delete_pending_message(cls, user_id: int, message_key: str = None):
        """حذف پیام در انتظار پاسخ"""
        session = session_manager.get_user_session(user_id, namespace=cls.PENDING_MESSAGES_NAMESPACE)
        
        if message_key:
            session.pop(message_key, None)
        else:
            # حذف همه پیام‌ها
            keys_to_delete = [k for k in session.keys() if k.startswith("msg_")]
            for key in keys_to_delete:
                del session[key]
        
        session_manager.set_user_session(user_id, session, namespace=cls.PENDING_MESSAGES_NAMESPACE)



###########################################################


class ForceReply:
    """Force reply markup for Balethon"""
    def __init__(self, selective: bool = False):
        self.force_reply = True
        self.selective = selective
    
    def to_dict(self):
        return {
            "force_reply": self.force_reply,
            "selective": self.selective
        }
    
    def __repr__(self):
        return f"ForceReply(selective={self.selective})"
    

###########################################################

from AI.settings import SITE_DOMAIN
from django.core.cache import cache
from accounts.models import ProfileModel
from products.models import Product
from payment.models import Cart, CartItem
from utils.balebot.api_client import BaleAPIClient



class ProductHandler:
    """Product Message and data handler Core"""

    def __init__(self, bot, product, current_site, photos=None, attributes=None):
        self.bot = bot
        self.product = product
        self.current_site = SITE_DOMAIN
        self.photos = photos or []
        self.attributes = attributes
        self._variants_data_cache = None
        self.client = BaleAPIClient(base_url="http://127.0.0.1:8000")
        

    async def handle_add_to_cart(self, call):
        """مدیریت افزودن به سبد خرید"""
        try:
            data = call.data.split("_")
            product_code = str(data[-1])

            if len(data) < 2:
                self.bot.answer_callback_query(call.id, "داده‌های نامعتبر!", show_alert=True)    #PEESIAN
                return
                
            if not product_code:
                self.bot.answer_callback_query(call.id, "کد محصول نامعتبر است!", show_alert=True)    #PERSIAN
                return

            chat_id = call.message.chat.id
            message_id = call.message.message_id

            # add product
            profile = await self.get_profile(chat_id)
            cart = await self.get_cart(chat_id)            
            
            
            
        

            variant_states = self.get_variant_states(chat_id=chat_id, product_code=product_code)
            print(f"variant states: {variant_states}")
            variants_dict = await self.get_variants_dict(await self._variant_details(product_code))
            print(f"variant dict : {variants_dict}")
            selected_values = self.build_selected_values(variants_dict, variant_states)


            variant = None
            if selected_values:
                variant = self.get_variant_by_selected_values(selected_values)

            cart_item = None
            # if variant:
            #     cart_item = CartItem.objects.filter(cart=cart, product=product, variant=variant).first()
            # else:
            #     if not product.variants.exists():
            #         cart_item = CartItem.objects.filter(cart=cart, product=product, variant__isnull=True).first()

            # if not cart_item:
            #     cart_item = CartItem.objects.create(
            #         cart=cart, 
            #         product=product,
            #         variant=variant,
            #         quantity=0
            #     )

            await self.update_product_message(chat_id, message_id, product_code)
            
        except Exception as e:
            print(f"❌ Error in handle_add_to_cart: {traceback.format_exc()}")

    async def handle_buttons(self, call):
        """مدیریت دکمه‌های افزایش/کاهش با در نظر گرفتن واریانت"""
        try:
            data = call.data.split("_")
            action = data[0]  # increase یا decrease
            product_code = str(data[1])
            variant_id = str(data[2]) if len(data) > 2 else "0"
            
            chat_id = call.message.chat.id
            message_id = call.message.message_id

            profile = await self.get_profile(chat_id)
            cart= await self.get_cart(chat_id)

            user_session = session_manager.get_user_session(chat_id, namespace="variants")
            variant_states = user_session.get(str(product_code), {})

            variants_dict =await self.get_variants_dict(await self._variant_details(product_code))
            selected_values = {}
            
            for i, key in enumerate(variants_dict.keys()):
                if str(i) in variant_states:
                    values_list = list(variants_dict[key])
                    selected_index = variant_states[str(i)]
                    if selected_index < len(values_list):
                        selected_values[key] = values_list[selected_index]

            # 🆕 پیدا کردن واریانت بر اساس variant_id از callback_data
            variant = None
            if variant_id != "0":
                try:
                    variant = ProductVariant.objects.get(id=variant_id, product=product)
                except ProductVariant.DoesNotExist:
                    print(f"Variant with id {variant_id} not found, using selected values")
                    # اگر variant_id پیدا نشد، از selected_values استفاده کن
                    if selected_values:
                        variant = self.get_variant_by_selected_values(product, selected_values)
            elif selected_values:
                # اگر variant_id نداریم اما selected_values داریم
                variant = self.get_variant_by_selected_values(product, selected_values)

            # 🆕 جستجوی دقیق CartItem بر اساس محصول و واریانت
            cart_item = None
            if variant:
                cart_item = CartItem.objects.filter(
                    cart=cart, 
                    product=product, 
                    variant=variant
                ).first()
            else:
                # اگر واریانت نداریم
                cart_item = await self.client._request(
                    endpoint="/myapi/cartitems/find/",
                    method="GET",
                    payload={
                        "cart": cart["id"],
                        "product": self.product["id"],
                        "variant": ""
                    }
                )
                cart_item = cart_item.data

            should_show_initial = False
            if action == "increase":
                if cart_item == {}:
                    # ایجاد آیتم جدید با واریانت صحیح
                    cart_item = await self.client._request(
                        endpoint="/myapi/cart/add-item/",
                        method="POST",
                        payload={
                            "product_id": self.product["id"],
                            "variant_id": variant["id"],
                            "quantity": 1,
                            "bale_id": chat_id,
                        }
                    )
                else:
                    if not variant:
                        a = {}
                        for i, (key, values) in enumerate(variants_dict.items()):
                            a[key] = values[0]
                        variant = await self.get_variant_by_selected_values(self.product, a)
                    max_stock = variant.stock if variant else self.product["stock"]

                    print(cart_item)
                    if cart_item["quantity"] < max_stock:
                    
                        await self.client._request(
                            endpoint="/myapi/cart/update-item/",
                            method="POST",
                            payload={
                                "item_id": cart_item["id"],
                                "quantity": cart_item["quantity"] + 1
                            }
                        )
                    else:
                        self.bot.answer_callback_query(
                            call.id, 
                            t(call.message, "max_stock_limit", max_stock=max_stock),
                            show_alert=True
                        )
                        return
                        
            elif action == "decrease":
                if cart_item:
                    if cart_item.quantity > 1:
                        cart_item.quantity -= 1
                        cart_item.save()
                    elif cart_item.quantity == 1:
                        cart_item.quantity = 0
                        cart_item.save()
                    elif cart_item.quantity == 0:
                        cart_item.delete()
                        should_show_initial = True
                        self.bot.answer_callback_query(call.id, t(call.message, "cart_item_removed"))
                else:
                    should_show_initial = True

            if should_show_initial:
                self.show_initial_state(chat_id, message_id, product)
            else:
                await self.update_product_message(chat_id, message_id, self.product)

        except ValidationError as ve:
            max_stock = variant.stock if variant else product["stock"]
            self.bot.answer_callback_query(
                call.id, 
                t(call.message, "max_stock_limit", max_stock=max_stock), 
                show_alert=True
            )
            return
        except Exception as e:
            print(f"Error in handle_buttons: {traceback.format_exc()}")

    async def update_product_message(self, chat_id, message_id, product_code):
        """آپدیت پیام محصول با در نظر گرفتن واریانت"""
        try:
            variants_dict = await self.get_product_variants_data()
            variant_states = self.get_variant_states(chat_id=chat_id, product_code=product_code)

            cart = await self.get_cart(chat_id=chat_id)
            variant = None
            current_quantity = 0
            cart_item_exists = False
            selected_values = None
            
            if selected_values:
                variant = self.get_variant_by_selected_values(product, selected_values)

            # 🆕 جستجوی دقیق CartItem
            cart_item = None
            if variant:
                cart_item = CartItem.objects.filter(
                    cart=cart, 
                    product=self.product, 
                    variant=variant
                ).first()
            else:
                cart_item = await self.get_cart_item(cart_id=cart["id"], product_id=self.product["id"])

            if cart_item:
                current_quantity = cart_item["quantity"]
                cart_item_exists = True

            buttons = []
            handlers = {}

            # 🆕 اضافه کردن variant_id به callback_dataهای افزایش/کاهش
            variant_id = variant.id if variant else "0"
            buttons.extend([
                ("➕", f"increase_{self.product["code"]}_{variant_id}", 0),
                (f"{current_quantity}", "count", 1),
                ("➖", f"decrease_{self.product["code"]}_{variant_id}", 2),
            ])
            
            handlers = {
                f"increase_{self.product["code"]}_{variant_id}": self.handle_buttons,
                f"decrease_{self.product["code"]}_{variant_id}": self.handle_buttons,
            }
            variants_dict = variants_dict["variants_dict"]
            
            # دکمه‌های واریانت
            for i, (key, values) in enumerate(variants_dict.items()):
                current_index = variant_states.get(str(i), 0)
                current_value = values[current_index] if current_index < len(values) else values[0]

                buttons.extend([
                    ("⏪", f"VarPrev_{self.product["code"]}_{i}", i * 3 + 5),
                    (f"{key}: {current_value}", f"var_{i}", i * 3 + 4),
                    ("⏩", f"VarNext_{self.product["code"]}_{i}", i * 3 + 3),
                ])
                
                handlers[f"VarPrev_{self.product["code"]}_{i}"] = self.handle_variant_navigation
                handlers[f"VarNext_{self.product["code"]}_{i}"] = self.handle_variant_navigation

            # دکمه سبد خرید
            total_cart_items = cart["total_items"]
            buttons.append((f"{await t("message", "menu_cart", chat_id=chat_id)} ({total_cart_items})", "view_cart", len(buttons) + 2))
            
            # لیآوت
            if variants_dict:
                button_layout = [3] + [3] * len(variants_dict) + [1]
            else:
                button_layout = [3, 1]

            stock_info = variant.stock if variant else self.product["stock"]
            if not variant:
                a = {}
                for i, (key, values) in enumerate(variants_dict.items()):
                    a[key] = values[0]
                variant = await self.get_variant_by_selected_values(self.product, a)
            stock_info = variant["stock"] if variant else self.product["stock"]

            text = await t("message", "order_up_to_stock", chat_id=chat_id, stock_info=stock_info)

            markup = SendMarkup(
                bot=self.bot,
                chat_id=chat_id,
                text=text,
                buttons=buttons,
                button_layout=button_layout,
                handlers=handlers,
            )
            
            await markup.edit(message_id)

        except Exception as e:
            print(f"❌ Error in update_product_message: {traceback.format_exc()}")

    
    async def get_profile(self, chat_id):
        response = await self.client._request(
            method="GET",
            endpoint=f"/myapi/profiles/{chat_id}/"
        )

        if response.success:
            return response.data

        else:
            profile = None
            result = await self.bot.send_message(chat_id, await t(call.message, "product_not_found"))    #PERSIAN
            return result



    
    async def get_cart(self, chat_id):
        response = await self.client._request(
            method="GET",
            endpoint=f"myapi/carts/by-profile/?bale_id={chat_id}"
        )
        return response.data["cart"] if response.success else None


    async def get_cart_item(self, cart_id, product_id=None, variant_id=None):
        endpoint = f"myapi/cartitems/find/?cart={cart_id}"

        if product_id:
            endpoint += f"&product={product_id}"

        if variant_id:
            endpoint += f"&variant={variant_id}"

        response = await self.client._request(method="GET", endpoint=endpoint)

        return response.data if response.success else None



    def get_variant_states(self, chat_id, product_code):
        user_session = session_manager.get_user_session(chat_id, namespace="variants")

        return user_session.get(str(product_code),{})

    def build_selected_values(self, variants_dict, variant_states):
        
        selected_values = {}

        for i, key in enumerate(variants_dict.keys()):
            if str(i) in variant_states:
                values_list = list(variants_dict[key])
                selected_index = variant_states[str(i)]
                if selected_index < len(values_list):
                    selected_values[key] = values_list[selected_index]

        return selected_values


    def resolve_selected_variant(self, product, chat_id):
        variant_states = self.get_variant_states(
            chat_id,
            product["code"]
        )

        variants_data = self.get_variants_dict()

        selected_values = self.build_selected_values(
            variants_data,
            variant_states
        )

        if not selected_values:
            return None

        return self.get_variant_by_selected_values(
            product,
            selected_values
        )


    async def _variant_details(self, code):
        product_variants = await self.client._request(method="POST", endpoint=f"myapi/products/variants/", payload={"product_code": self.product["code"]})
        product_variants = product_variants.data
        return product_variants



    async def get_product_variants_data(self):
        """Get all variant data with caching"""

        if self._variants_data_cache:
            return self._variants_data_cache

        cache_key = f"product_{self.product['id']}_full_variants_data"
        cached_data = cache.get(cache_key)

        if cached_data:
            self._variants_data_cache = cached_data
            return cached_data

        variants_dict = {}
        variants_list = []

        variants = await self._variant_details(code=self.product["code"])

        for variant in variants:
            variant_data = {
                'id': variant["id"],
                'sku': variant["sku"],
                'stock': variant["stock"],
                'price_override': variant["price_override"],
                'values': {}
            }

            for option_value in variant["values"]:
                key = option_value["option_name"].capitalize()
                value = option_value["value"]

                variant_data['values'][key] = value

                if key not in variants_dict:
                    variants_dict[key] = set()

                variants_dict[key].add(value)

            variants_list.append(variant_data)

        def sort_variant_values(values):
            numeric = []
            strings = []

            for v in values:
                try:
                    numeric.append(float(v) if '.' in str(v) else int(v))
                except:
                    strings.append(str(v))

            return list(map(str, sorted(numeric))) + sorted(strings)

        result = {
            'variants_dict': {key: sort_variant_values(values) for key, values in variants_dict.items()},
            'variants_list': variants_list}


        cache.set(cache_key, result, timeout=300)
        self._variants_data_cache = result


        return result


    async def get_variants_dict(self, variants=None):
        """تبدیل واریانت‌ها به دیکشنری - کاملاً از کش استفاده می‌کند"""
        variants_data = await self.get_product_variants_data()
        return variants_data['variants_dict']
    
    async def _all_varaints(self):
        all_product_variants = await self.client._request(method="GET", endpoint=f"myapi/productvariants/")
        all_product_variants = all_product_variants.data
        return all_product_variants


    async def get_variant_by_selected_values(self, selected_values):
        """پیدا کردن واریانت بر اساس مقادیر انتخاب شده"""
        variants_data = await self.get_product_variants_data()
        print(variants_data)
        
        print(f"🔍 [VARIANT DEBUG] Looking for variant with: {selected_values}")
        print(f"🔍 [VARIANT DEBUG] Total variants: {len(variants_data['variants_list'])}")
        
        for variant_data in variants_data['variants_list']:
            variant_values = variant_data['values']
            
            # بررسی تطابق کامل
            match = True
            for key, selected_value in selected_values.items():
                variant_value = variant_values.get(key)
                
                if not variant_value:
                    match = False
                    break
                    
                selected_clean = str(selected_value).strip().lower()
                variant_clean = str(variant_value).strip().lower()
                
                if selected_clean != variant_clean:
                    match = False
                    break
            
            if match:
                print(f"✅ [VARIANT DEBUG] EXACT MATCH FOUND: {variant_data['id']}")
                from products.models import ProductVariant
                return ProductVariant.objects.get(id=variant_data['id'])
        
        print("❌ [VARIANT DEBUG] No exact matching variant found")
        return None



#########################################  MAIN METHODS  #########################################



    async def format_price(self):
        """فرمت‌بندی قیمت بدون کوئری دیتابیس"""
        formatted_price = "{:,.0f}".format(float(self.product["price"]))
        formatted_final_price = "{:,.0f}".format(float(self.product["final_price"]))
        
        if int(float(self.product["discount"])) > 0:
            return (
                f"🏃 {self.product["discount"]} % تخفیف\n"
                f"💵 {await t('message', 'price')}:\n❌ {formatted_price} تومان ❌   ⬅   ✅ {formatted_final_price} تومان ✅"
            )
        return f"💵 {await t('message', 'price')}: {formatted_price} تومان"

    
    # def build_attributes_text(self):
    #     if not self.attributes:
    #         return ""
    #     return "\n".join(
    #         [f"✨ {a.key}: {a.value}" if a.value else f"✨ {a.key}" for a in self.attributes]
    #     ) + "\n\n"


    # def build_variants_text(self, variants_dict):
    #     if not variants_dict:
    #         return ""
    #     lines = [
    #         f"✅ {key}: {', '.join(values)}"
    #         for key, values in variants_dict.items()
    #     ]
    #     return "\n".join(lines) + "\n\n"


    # async def async_get_product_variants_data(self):
    #     variants = await sync_to_async(list)(
    #         self.product["variants.prefetch_related("values__option").all()
    #     )

    #     variants_dict = defaultdict(set)

    #     for variant in variants:
    #         values = await sync_to_async(list)(variant.values.all())
    #         for val in values:
    #             variants_dict[val.option.name].add(val.value)

    #     return {
    #         "variants_dict": {
    #             k: sorted(list(v)) for k, v in variants_dict.items()
    #         }
    #     }



    async def generate_caption(self):
        brand_text = f"🔖 برند کالا: {self.product["brand"]}\n" if self.product["brand"] else ""
        description_text = f"{self.product["description"]}\n" if self.product["description"] else ""
    
        # Attributes
        # attribute_text = ""
        # if self.attributes:
        #     attribute_text = "\n✨ ".join(
        #         [f"{attr.key}: {attr.value}" if attr.value else f"{attr.key}" for attr in self.attributes]
        #     )
        #     attribute_text = f"✨ {attribute_text}\n\n"
    
        # واریانت‌ها
        # variants_data = await self.async_get_product_variants_data()
    
        # variants_text = ""
        # if variants_data['variants_dict']:
            # variant_lines = [
            #     f"{key}: {', '.join(values)}"
            #     for key, values in variants_data['variants_dict'].items()
            # ]
            # variants_text = "✅ " + "\n✅ ".join(variant_lines) + "\n\n"
    
        # قیمت (sync_to_async درست)
        price_text = await self.format_price()
        
        return (
            f"\n⭕️ نام کالا: {self.product["name"]}\n"
            f"{brand_text}"
            f"کد کالا: {self.product["code"]}\n\n"
            f"{description_text}\n"
            # f"{attribute_text}"
            # f"{variants_text}"
            f"📫 ارسال به تمام نقاط کشور\n\n"
            f"{price_text}\n"
        )




    # async def send_product_channel(self, chat_id, buttons=True):
    #     try:
    #         caption = await self.async_generate_caption()

    #         if not self.photos:
    #             await self.bot.send_message(
    #                 chat_id,
    #                 caption,
    #                 parse_mode="html",
    #                 buttons=[[Button.inline("🛒 خرید", b"buy_now")]] if buttons else None
    #             )
    #             return

    #         files = [await self.bot.upload_file(p) for p in self.photos]

    #         await self.bot.send_file(
    #             chat_id,
    #             files,
    #             caption=caption,
    #             parse_mode="html",
    #             supports_streaming=True
    #         )

    #         if buttons:
    #             await self.bot.send_message(
    #                 chat_id,
    #                 "👇👇👇",
    #                 buttons=[[Button.inline("🛒 خرید", b"buy_now")]]
    #             )

    #     except Exception:
    #         print("❌ send_product_channel error:\n", traceback.format_exc())




    async def send_product_message(self, message, buttons=True):
        """Send product media group with optional action buttons."""
        import re

        try:
            # Extract a valid media URL from a local path or malformed URL
            def extract_url(path_or_url):
                if path_or_url.startswith('/home/'):
                    match = re.search(r'/media/(.+)', path_or_url)
                    if match:
                        return f"http://192.168.1.141/media/{match.group(1)}"

                elif (
                    'http://192.168.1.141' in path_or_url
                    and path_or_url.startswith('/home')
                ):
                    match = re.search(
                        r'(http://192.168.1.141/media/[^\s\']+)',
                        path_or_url
                    )
                    if match:
                        return match.group(1)

                return path_or_url

            media_list = []

            # Process main product image
            main_image_url = self.product["main_image"]

            if not main_image_url.startswith('http'):
                main_image_url = extract_url(main_image_url)

            # Generate product caption
            caption_text = await self.generate_caption()

            # Add main image with caption
            media_list.append({
                "type": "photo",
                "media": main_image_url,
                "caption": caption_text,
                "parse_mode": "HTML"
            })

            # Add additional images (up to Telegram limit)
            for img in self.product["images"]:
                if len(media_list) >= 10:
                    break

                img_url = img["image"]

                if not img_url.startswith('http'):
                    img_url = extract_url(img_url)

                media_list.append({
                    "type": "photo",
                    "media": img_url
                })

            # Send media group
            result = await self.bot.send_media_group(
                chat_id=message.chat.id,
                media=media_list
            )

            # Send action buttons if requested
            if buttons:
                await self.send_buttons(message)

            return result

        except Exception:
            print(f"Error details: {traceback.format_exc()}")
            return None   

    async def send_buttons(self, message):
        """ارسال سریع دکمه‌ها بدون تأخیر"""
        try:
            # محاسبه سریع داده‌های مورد نیاز
            # buttons_data = self._prepare_buttons_data(message.chat.id)
            # if not buttons_data:
            #     return
                
            # ارسال فوری دکمه‌ها
            result = await self._send_buttons_from_data(message)
            
        except Exception as e:
            print(f"Error in send_buttons: {traceback.format_exc()}")

    # def _prepare_buttons_data(self, chat_id):
    #     """آماده‌سازی سریع داده‌های دکمه"""
    #     try:
    #         # دریافت session
    #         session = SessionManager()
    #         user_session = session.get_user_session(chat_id, namespace="variants")
    #         variant_states = user_session.get(str(self.product["code), {})
            
    #         # کوئری‌های موازی برای داده‌های ضروری
    #         profile = ProfileModel.objects.get(tel_id=chat_id)
    #         cart, _ = Cart.objects.get_or_create(profile=profile)
            
    #         # استفاده از داده‌های کش شده
    #         variants_dict = self.get_variants_dict(self.product.variants.all())
            
    #         # محاسبه سریع مقادیر انتخاب شده
    #         selected_values = {}
    #         for i, key in enumerate(variants_dict.keys()):
    #             if str(i) in variant_states:
    #                 values_list = list(variants_dict[key])
    #                 selected_index = variant_states[str(i)]
    #                 if selected_index < len(values_list):
    #                     selected_values[key] = values_list[selected_index]
            
    #         # پیدا کردن واریانت
    #         variant = None
    #         if selected_values:
    #             variant = self.get_variant_by_selected_values(self.product, selected_values)
            
    #         # وضعیت سبد خرید
    #         current_quantity = 0
    #         cart_item_exists = False
            
    #         if variant:
    #             cart_item = CartItem.objects.filter(
    #                 cart=cart, 
    #                 product=self.product, 
    #                 variant=variant
    #             ).first()
    #             if cart_item:
    #                 current_quantity = cart_item.quantity
    #                 cart_item_exists = True
    #         else:
    #             cart_item = CartItem.objects.filter(
    #                 cart=cart, 
    #                 product=self.product, 
    #                 variant__isnull=True
    #             ).first()
    #             if cart_item:
    #                 current_quantity = cart_item.quantity
    #                 cart_item_exists = True

    #         return {
    #             'variant_states': variant_states,
    #             'cart': cart,
    #             'variants_dict': variants_dict,
    #             'selected_values': selected_values,
    #             'variant': variant,
    #             'current_quantity': current_quantity,
    #             'cart_item_exists': cart_item_exists
    #         }
            
    #     except Exception as e:
    #         print(f"Error in _prepare_buttons_data: {traceback.format_exc()}")
    #         return None

    async def _send_buttons_from_data(self, message, buttons_data=None):   # =None is added temporarely
        """ارسال فوری دکمه‌ها با داده‌های از پیش محاسبه شده"""
        try:
            # print(buttons_data)
            # variant_states = buttons_data['variant_states']
            # cart = buttons_data['cart']
            # variants_dict = buttons_data['variants_dict']
            # variant = buttons_data['variant']
            # current_quantity = buttons_data['current_quantity']
            # cart_item_exists = buttons_data['cart_item_exists']

            # ساخت سریع دکمه‌ها
            buttons = []
            handlers = {}
            
            # if cart_item_exists:
                # حالت شمارنده
                # variant_id = variant.id if variant else "0"
                # buttons.extend([
                #     ("➕", f"increase_{self.product["code"]}_{variant_id}", 2),
                #     (f"{current_quantity}", "count", 1),
                #     ("➖", f"decrease_{self.product["code"]}_{variant_id}", 0),
                # ])
                
                # handlers.update({
                #     f"increase_{self.product["code"]}": self.handle_buttons,
                #     f"decrease_{self.product["code"]}": self.handle_buttons,
                # })
                
                # دکمه‌های واریانت
                # for i, (key, values) in enumerate(variants_dict.items()):
                #     current_index = variant_states.get(str(i), 0)
                #     current_value = values[current_index] if current_index < len(values) else values[0]
                    
                #     buttons.extend([
                #         ("⏪", f"VarPrev_{self.product["code"]}_{i}", i * 3 + 3),
                #         (f"{key}: {current_value}", f"var_{i}", i * 3 + 4),
                #         ("⏩", f"VarNext_{self.product["code"]}_{i}", i * 3 + 5),
                #     ])
                    
                #     handlers.update({
                #         f"VarPrev_{self.product["code"]}_{i}": self.handle_variant_navigation,
                #         f"VarNext_{self.product["code"]}_{i}": self.handle_variant_navigation,
                #     })

                # دکمه سبد خرید
                # total_cart_items = cart.total_items()
                # buttons.append((f"{t("message", "menu_cart", chat_id=chat_id)} ({total_cart_items})", "view_cart", len(buttons) + 2))
                
                # لیآوت
                # if variants_dict:
                #     button_layout = [3] + [3] * len(variants_dict) + [1]
                # else:
                    # button_layout = [3, 1]
                    
            # else:
                # حالت اولیه
            buttons.extend([
                (await t(message, "add_to_cart"), f"addtocart_{self.product["code"]}", 1),
                (await t(message, "comments"), f"comments_{self.product["code"]}", 0),
            ])

                
            handlers.update({
                f"addtocart_{self.product["code"]}": self.handle_add_to_cart,
                f"comments_{self.product["code"]}": "self.handle_comments",
            })
                
            button_layout = [2]

            variant = None

            # متن اطلاع‌رسانی
            # stock_info = variant.stock if variant else self.product["stock"]
            # print("_send_buttons_from_data")
            text = await t(message, "order_up_to_stock", stock_info=self.product["stock"])
            
            # ارسال فوری
            markup = SendMarkup(
                bot=self.bot,
                chat_id=message.chat.id,
                text=text,
                buttons=buttons,
                button_layout=button_layout,
                handlers=handlers
            )
            result = await markup.send()
            return result
            
        except Exception as e:
            print(f"Error in _send_buttons_from_data: {traceback.format_exc()}")

    # def _send_buttons_safe(self, chat_id):
    #     """متد قدیمی برای سازگاری - حالا از نسخه سریع استفاده می‌کند"""
    #     self.send_buttons(chat_id)

    # def show_initial_state(self, chat_id, message_id, product):
    #     """نمایش حالت اولیه"""
    #     try:
    #         buttons = [
    #             (t("message", "add_to_cart", chat_id=chat_id), f"addtocart_{product["code"]}", 1),
    #             (t("message", "comments", chat_id=chat_id), f"comments_{product["code"]}", 0),
    #         ]
            
    #         handlers = {
    #             f"addtocart_{product["code"]}": self.handle_add_to_cart,
    #             f"comments_{product["code"]}": self.handle_comments,
    #         }
            
    #         stock_info = product["stock"]
    #         print("initail state")
    #         text = t("message", "order_up_to_stock", chat_id=chat_id, stock_info=stock_info)

    #         markup = SendMarkup(
    #             bot=self.bot,
    #             chat_id=chat_id,
    #             text=text,
    #             buttons=buttons,
    #             button_layout=[2],
    #             handlers=handlers,
    #         )
            
    #         markup.edit(message_id)

    #     except Exception as e:
    #         print(f"❌ Error in show_initial_state: {traceback.format_exc()}")

    


    def handle_variant_navigation(self, call):
        """مدیریت ناوبری واریانت‌ها"""
        try:
            parts = call.data.split("_")
            action_type = parts[0]
            product_code = parts[1]
            variant_index = int(parts[2])

            chat_id = call.message.chat.id
            message_id = call.message.message_id

            profile = ProfileModel.objects.get(tel_id=chat_id)
            cart, _ = Cart.objects.get_or_create(profile=profile)

            session = SessionManager()
            user_session = session.get_user_session(chat_id, namespace="variants")
            variant_states = user_session.get(str(product_code), {})

            variants_dict = self.get_variants_dict(self.product.variants.all())
            variant_keys = list(variants_dict.keys())

            if variant_index >= len(variant_keys):
                self.bot.answer_callback_query(call.id, "خطا در یافتن واریانت!", show_alert=True)
                return

            current_key = variant_keys[variant_index]
            values = list(variants_dict[current_key])
            current_state = variant_states.get(str(variant_index), 0)

            if action_type == "VarPrev":
                current_state = (current_state - 1) % len(values)
            elif action_type == "VarNext":
                current_state = (current_state + 1) % len(values)

            variant_states[str(variant_index)] = current_state
            user_session[str(product_code)] = variant_states
            session.set_user_session(chat_id, user_session, namespace="variants")

            self.update_product_message(chat_id, message_id, self.product, cart)
            
            current_value = values[current_state]
            self.bot.answer_callback_query(call.id, f"{current_key} به {current_value} تغییر کرد")

        except Exception as e:
            print(f"Error in handle_variant_navigation: {traceback.format_exc()}")
            self.bot.answer_callback_query(call.id, "خطا در تغییر واریانت!", show_alert=True)

    # def handle_comments(self, call):
    #     """مدیریت دکمه نظرات"""
    #     try:
    #         chat_id = call.message.chat.id
    #         self.bot.send_message(chat_id, "صفحه نظرات محصول...")
    #         self.bot.answer_callback_query(call.id)
    #     except Exception as e:
    #         print(f"Error in handle_comments: {traceback.format_exc()}")
