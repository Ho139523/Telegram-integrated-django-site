from attr import attributes
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import json, traceback, asyncio, requests, base64
from telebot import TeleBot, types
from telethon import TelegramClient
from telethon.sessions import StringSession
from django.core.cache import cache
from django.conf import settings
from asgiref.sync import sync_to_async
from AI.settings import current_site as settings_current_site

# 🧩 مدل‌ها و پکیج‌های پروژه
from .zarinpal import ZarinPal
from products.models import Product
from accounts.models import ProfileModel
from payment.models import Transaction, Sale, Cart, CartItem
from utils.variables.TOKEN import TOKEN, api_id, api_hash, BOT_ID
from products.signals import t, async_helper
from django.db import transaction as db_transaction

# 🟩 تنظیمات عمومی
pay = ZarinPal()
bot = TeleBot(TOKEN)
SESSION_STRING = settings.TG_SESSION_STRING
API_ID = api_id
API_HASH = api_hash


# ==========================================================
# 🧩 تابع ارسال آلبوم محصول (با حالت اتمام موجودی یا معمولی)
# ==========================================================

async def send_album_and_button_async(channel_id, product, photos, out_of_stock=False):
    """ارسال آلبوم محصول با کپشن مشابه ProductHandler و دکمه خرید یا درخواست موجود کردن"""
    print(f"\n🚀 [send_album_and_button_async] Sending product {product.name} | out_of_stock={out_of_stock}")
    try:
        client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
        await client.connect()

        if not await client.is_user_authorized():
            print("⚠️ Telethon session not authorized!")
            return

        # 🖼️ آپلود تصاویر
        media = []
        for path in photos:
            try:
                file = await client.upload_file(path)
                media.append(file)
                print(f"📷 Uploaded image: {path}")
            except Exception as e:
                print(f"⚠️ Failed to upload {path}: {e}")

        # ✏️ خواندن فیلدها به‌صورت امن از ORM
        brand = await sync_to_async(lambda: product.brand)()
        description = await sync_to_async(lambda: product.description)()
        attributes = await sync_to_async(lambda: list(product.attributes.all()))()
        discount = await sync_to_async(lambda: product.discount)()
        price = await sync_to_async(lambda: product.price)()
        final_price = await sync_to_async(lambda: product.final_price)()

        # ساخت متن‌ها
        brand_text = f"🔖 برند کالا: {brand}\n" if brand else ""
        description_text = f"{description}\n" if description else ""

        attribute_text = ""
        if attributes:
            attribute_text = "\n✅ ".join(
                [f"{attr.key}: {attr.value}" if attr.value else f"{attr.key}" for attr in attributes]
            )
            attribute_text = f"✅ {attribute_text}\n\n"

        # اگر محصول تمام شده باشد
        if out_of_stock:
            formatted_price = "{:,.0f}".format(float(price))
            formatted_final_price = "{:,.0f}".format(float(final_price))
            if discount > 0:
                price_text = (
                    f"🏃 {discount}% تخفیف\n"
                    f"💵 قیمت: <s>{formatted_price}</s> تومان ⬅ {formatted_final_price} تومان"
                )
            else:
                price_text = f"💵 قیمت: {formatted_price} تومان"
            price_text += "\n❌❌  <b style={fontsize:45;}>اتمام موجودی</b>  ❌❌\n❌❌ <b style={fontsize:45;}>اتمام موجودی</b>  ❌❌\n❌❌  <b style={fontsize:45;}>اتمام موجودی</b>  ❌❌\n\n"
            formatted_price = "{:,.0f}".format(float(price))
            formatted_final_price = "{:,.0f}".format(float(final_price))
            

        caption = (
            f"\n⭕️ <b>نام کالا:</b> {product.name}\n"
            f"{brand_text}"
            f"<b>کد کالا:</b> {product.code}\n\n"
            f"{description_text}\n"
            f"{attribute_text}"
            f"{price_text}\n"
        )

        # 🧩 ساخت دکمه
        markup = types.InlineKeyboardMarkup()
        owner_lang, store_id, product_id = await async_helper(product)

        if out_of_stock:
            #ترجمه‌ی متن دکمه ---
            request_product_text = await t(owner_lang, "request_restock")
            markup.add(types.InlineKeyboardButton(request_product_text, callback_data=f"request_{product.id}"))
        else:
            markup.add(types.InlineKeyboardButton("🛒 همین حالا بخرش", url=f"https://intelium.ir/buy/?pid={product.id}"))

        # 📤 ارسال آلبوم
        if media:
            await client.send_file(channel_id, media, caption=caption, parse_mode="HTML")
        else:
            await client.send_message(channel_id, caption, parse_mode="HTML")

        # ارسال دکمه با ربات
        bot.send_message(channel_id, "👇👇👇👇👇👇👇👇", reply_markup=markup)

        print("✅ [send_album_and_button_async] Message sent successfully.\n")
        await client.disconnect()

    except Exception as e:
        print(f"❌ Error in send_album_and_button_async: {e}")
        traceback.print_exc()


def send_album_and_button(channel_id, product, photos, out_of_stock=False):
    """نسخه sync برای استفاده در Django"""
    print(f"⚙️ [send_album_and_button] channel={channel_id}, product={product.name}, out_of_stock={out_of_stock}")
    try:
        asyncio.run(send_album_and_button_async(channel_id, product, photos, out_of_stock))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(send_album_and_button_async(channel_id, product, photos, out_of_stock))
    except Exception as e:
        print(f"⚠️ send_album_and_button() failed: {e}")
        traceback.print_exc()


# ==========================================================
# 💳 درخواست پرداخت
# ==========================================================
@csrf_exempt
def send_request(request):
    if request.method == 'GET':
        try:
            payment_id = request.GET.get('pid')
            print(f"Payment ID: {payment_id}")

            payment_data = cache.get(f'payment_{payment_id}')
            if not payment_data:
                return JsonResponse({'error': 'لینک پرداخت منقضی شده است'}, status=400)

            tel_id = payment_data['tel_id']
            profile = ProfileModel.objects.get(tel_id=tel_id)
            cart = Cart.objects.get(profile=profile)
            cart_items = CartItem.objects.filter(cart=cart)

            if not cart_items.exists():
                return JsonResponse({"error": "سبد خرید خالی است"}, status=400)

            # محاسبه مبلغ کل (به ریال)
            amount = sum(item.total_price() for item in cart_items) * 10
            
            # محاسبه تقسیم‌های پرداخت
            splits = []
            sellers_split = cart.get_sellers_split()
            
            for seller, seller_amount in sellers_split.items():
                if hasattr(seller, 'zarinpal_merchant_id') and seller.zarinpal_merchant_id:
                    splits.append({
                        "merchant_id": seller.zarinpal_merchant_id,
                        "amount": int(seller_amount * 10)  # تبدیل به ریال
                    })

            description = f"پرداخت سبد خرید شامل {cart_items.count()} کالا"

            # ارسال درخواست پرداخت با تقسیم
            if splits:
                response = pay.send_split_request(
                    amount=int(amount),
                    description=description,
                    splits=splits,
                    email=profile.email,
                    mobile=profile.phone
                )
            else:
                response = pay.send_request(
                    amount=int(amount),
                    description=description,
                    email="admin@admin.com",
                    mobile=profile.phone
                )

            if not response.get("success"):
                return JsonResponse({"error": response.get("message", "خطا در اتصال به درگاه")}, status=400)

            authority = response.get("authority")
            if not authority:
                return JsonResponse({"error": "Failed to get authority from ZarinPal"}, status=400)

            # ایجاد تراکنش
            transaction = Transaction.objects.create(
                profile=profile,
                cart=cart,
                amount=amount // 10,  # ذخیره به تومان
                authority=authority,
                status="pending"
            )
            
            # ایجاد تقسیم‌های پرداخت
            transaction.create_split_payments()

            cache.delete(f'payment_{payment_id}')
            return HttpResponseRedirect(response["url"])

        except Exception as e:
            print(f"Error in send_request: {e}")
            return JsonResponse({"error": f"Error: {traceback.format_exc()}"}, status=500)


# ==========================================================
# ✅ تایید پرداخت موفق
# ==========================================================
@csrf_exempt
def verify(request):
    try:
        authority = request.GET.get('Authority')
        status = request.GET.get('Status')

        if not authority:
            return JsonResponse({"error": "Missing authority"}, status=400)

        try:
            transaction = Transaction.objects.get(authority=authority)
        except Transaction.DoesNotExist:
            return JsonResponse({"error": "Transaction not found"}, status=404)

        if status != "OK":
            transaction.mark_as_canceled()
            return render(request, "payment/tel_payment_failed.html", {"message": "پرداخت لغو شد"})

        # تایید پرداخت
        response = pay.verify(authority=authority, amount=transaction.amount * 10)

        if response.get("success") and response.get("transaction"):
            transaction.status = "paid"
            transaction.zarinpal_ref_id = response.get("ref_id")
            transaction.save()
            
            # پردازش موفقیت‌آمیز پرداخت
            handle_successful_payment(transaction)
            return render(request, "payment/tel_payment_success.html")
        else:
            transaction.mark_as_failed()
            return render(request, "payment/tel_payment_failed.html", 
                         {"message": f"پرداخت ناموفق بود: {response.get('message', 'خطای ناشناخته')}"})

    except Exception as e:
        print(f"❌ Verify Error: {e}")
        return JsonResponse({"error": str(e)}, status=500)


# ==========================================================
# 🧩 تابع اصلی پردازش پرداخت موفق
# ==========================================================
def handle_successful_payment(transaction):
    try:
        if transaction.status == "paid" and transaction.cart:
            print(f"\n💳 PAYMENT SUCCESS - Transaction: {transaction.id}")
            
            # استفاده از transaction دیتابیس برای اطمینان از یکپارچگی داده‌ها
            with db_transaction.atomic():
                sales = []
                for cart_item in transaction.cart.items.all():
                    product = cart_item.product
                    
                    if product.stock >= cart_item.quantity:
                        # کاهش موجودی
                        product.stock -= cart_item.quantity
                        product.save(update_fields=["stock"])
                        
                        # ایجاد فروش
                        sale = Sale.objects.create(
                            transaction=transaction,
                            product=product,
                            seller=product.store,
                            quantity=cart_item.quantity,
                            unit_price=int(product.final_price),
                            total_price=int(cart_item.total_price())
                        )
                        sales.append(sale)
                        
                        # بررسی اتمام موجودی
                        if product.stock == 0 and product.store.tel_channel:
                            try:
                                photos = []
                                if product.main_image:
                                    photos.append(product.main_image.path)
                                photos += [img.image.path for img in product.images.all()]
                                
                                send_album_and_button(
                                    channel_id=product.store.tel_channel,
                                    product=product,
                                    photos=photos,
                                    out_of_stock=True
                                )
                            except Exception as ex:
                                print(f"⚠️ Error sending out-of-stock album: {ex}")

                # ارسال پیام‌ها
                send_payment_notifications(transaction, sales)
                
                # پاک کردن سبد خرید
                transaction.cart.items.all().delete()

    except Exception as e:
        print(f"❌ [handle_successful_payment] Error: {e}")
        traceback.print_exc()


def send_payment_notifications(transaction, sales):
    """ارسال پیام‌های اطلاع‌رسانی پس از پرداخت موفق"""
    try:
        chat_id_buyer = transaction.profile.tel_id
        telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        
        # پیام به خریدار
        buyer_products = "\n".join(
            [f"🔹 {s.product.name} × {s.quantity} = {s.total_price:,} تومان" for s in sales]
        )
        buyer_message = (
            "✅ پرداخت شما با موفقیت انجام شد!\n"
            f"🛍️ محصولات خریداری‌شده:\n{buyer_products}\n\n"
            f"💰 مبلغ کل: {transaction.amount:,} تومان\n"
            f"📋 کد پیگیری: {transaction.zarinpal_ref_id or '---'}"
        )
        
        requests.post(telegram_url, json={"chat_id": chat_id_buyer, "text": buyer_message})

        # پیام به فروشندگان
        sellers_map = {}
        for s in sales:
            seller_tel_id = s.seller.owner.tel_id
            if seller_tel_id:
                if seller_tel_id not in sellers_map:
                    sellers_map[seller_tel_id] = {"store": s.seller, "products": [], "total_income": 0}
                sellers_map[seller_tel_id]["products"].append(s)
                sellers_map[seller_tel_id]["total_income"] += s.total_price

        buyer_info = transaction.profile
        address = buyer_info.get_active_address()
        address_text = (
            f"{address.shipping_line1}, {address.shipping_city_name}, "
            f"{address.shipping_province_name}, {address.shipping_country_name}" if address else "نامشخص"
        )

        for chat_id_seller, data in sellers_map.items():
            seller_products = "\n".join(
                [f"🔹 {s.product.code} | {s.product.name} × {s.quantity} = {s.total_price:,} تومان"
                 for s in data["products"]]
            )
            seller_message = (
                f"📦 سفارش جدید در فروشگاه {data['store'].name}\n\n"
                f"{seller_products}\n\n"
                f"💰 مجموع درآمد شما: {data['total_income']:,} تومان\n\n"
                f"👤 خریدار: {buyer_info.fname} {buyer_info.lname}\n"
                f"📞 تلفن: {buyer_info.phone}\n"
                f"🏠 آدرس: {address_text}"
            )
            requests.post(telegram_url, json={"chat_id": chat_id_seller, "text": seller_message})

    except Exception as e:
        print(f"❌ Error sending notifications: {e}")

