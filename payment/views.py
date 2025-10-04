from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .zarinpal import ZarinPal
import json
from products.models import Product
from accounts.models import ProfileModel
from payment.models import Transaction, Sale, Cart, CartItem
import requests
from utils.variables.TOKEN import TOKEN, BOT_ID
from django.shortcuts import render
import base64
import traceback
from django.http import HttpResponseRedirect
from django.core.cache import cache

pay = ZarinPal()

@csrf_exempt
def send_request(request):
    if request.method == 'GET':
        try:
            # 1. دریافت شناسه پرداخت
            payment_id = request.GET.get('pid')
            print(payment_id)
            
            # 2. بازیابی داده از کش
            payment_data = cache.get(f'payment_{payment_id}')
            print(payment_data)
            
            if not payment_data:
                return JsonResponse({'error': 'لینک پرداخت منقضی شده است'}, status=400)
            
            # 3. پردازش پرداخت
            tel_id = payment_data['tel_id']


            profile = ProfileModel.objects.get(tel_id=tel_id)
            cart = Cart.objects.get(profile=profile)
            cart_items = CartItem.objects.filter(cart=cart)

            if not cart_items.exists():
                return JsonResponse({"error": "سبد خرید خالی است"}, status=400)
            
            amount = sum(item.total_price() for item in cart_items)*10
            description = f"پرداخت سبد خرید شامل {cart_items.count()} کالا"
            
            response = pay.send_request(
                amount=int(amount),
                description=description,
                email="admin@admin.com",
                mobile="09123456789"
            )
            
            authority = response.get("authority")
            if not authority:
                return JsonResponse({"error": "Failed to get authority from ZarinPal"}, status=400)
            
            # ایجاد تراکنش با ارجاع به سبد خرید
            transaction = Transaction.objects.create(
                profile=profile,
                cart=cart,
                amount=amount // 10,
                authority=authority,
                status="pending"
            )
            
            cache.delete(f'payment_{payment_id}')

            return HttpResponseRedirect(response["url"])
            
        except Exception as e:
            error_details = traceback.format_exc()
            return JsonResponse({"error": f"An internal error occurred. {str(error_details)}"}, status=500)



from django.shortcuts import render

@csrf_exempt
def verify(request):
    try:
        authority = request.GET.get('Authority')
        status = request.GET.get('Status')

        if not authority:
            return JsonResponse({"error": "Missing authority"}, status=400)

        # بازیابی تراکنش از دیتابیس
        try:
            transaction = Transaction.objects.get(authority=authority)
        except Transaction.DoesNotExist:
            return JsonResponse({"error": "Transaction not found"}, status=404)
        
        if status != "OK":
            transaction.mark_as_canceled()
            return render(request, "payment/tel_payment_failed.html", 
                        {"message": "پرداخت توسط کاربر لغو شد"})

        response = pay.verify(authority=authority, amount=transaction.amount * 10)
        

        if response.get("transaction") and response.get("pay"):
            transaction.status = "paid"  # تغییر وضعیت تراکنش
            transaction.save()
            handle_successful_payment(transaction)  # اجرای تابع پردازش پرداخت موفق
            return render(request, "payment/tel_payment_success.html")
        else:
            transaction.mark_as_failed()
            return render(request, "payment/tel_payment_failed.html", 
                        {"message": response.get("message", "پرداخت ناموفق بود")})

    except Exception as e:
        print(f"Verify Error: {str(e)}")
        return JsonResponse({"error": f"An internal error occurred. {str(e)}"}, status=500)



import asyncio
import traceback
import requests
from telethon import TelegramClient
from telethon.sessions import StringSession
from telebot import TeleBot
from utils.variables.TOKEN import TOKEN, api_id, api_hash, BOT_ID
from telethon.sessions import StringSession
from utils.telbot.functions import ProductHandler
from django.conf import settings

bot = TeleBot(TOKEN)
SESSION_STRING = settings.TG_SESSION_STRING
CURRENT_SITE = "https://intelium.ir:8443"
API_ID = api_id
API_HASH = api_hash


# 🟡 تابع ارسال پیام اتمام موجودی (غیرهمزمان)
async def send_out_of_stock_announcement(channel_id, product, photos):
    """
    ارسال پیام اتمام موجودی محصول به کانال با لاگ‌گذاری مرحله‌به‌مرحله
    """
    print(f"\n🚀 [send_out_of_stock_announcement] Starting for {product.name} in channel {channel_id}")
    try:
        print("🔹 Creating Telegram client...")
        client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
        await client.connect()

        if not await client.is_user_authorized():
            print("⚠️ [Telethon] Session not authorized! Please re-login.")
            return

        print("✅ [Telethon] Client connected and authorized successfully.")

        # --- 1. ارسال آلبوم محصول ---
        try:
            print("🖼️ [Step 1] Sending product album to channel...")
            handler = ProductHandler(client, product, CURRENT_SITE, photos=photos)
            await handler.send_product_channel(channel_id, buttons=False)
            print("✅ [Step 1] Product album sent successfully.")
        except Exception as album_err:
            print(f"❌ [Step 1 Error] Failed to send album: {album_err}")
            traceback.print_exc()

        # کمی صبر برای نظم ارسال پیام‌ها
        await asyncio.sleep(1.5)

        # --- 2. واکشی زبان و متن ترجمه‌شده ---
        try:
            print("🌍 [Step 2] Fetching store owner language...")
            owner_lang, store_id, product_id = await async_helper(product)
            print(f"✅ [Step 2] Language: {owner_lang}, Store ID: {store_id}, Product ID: {product_id}")
        except Exception as lang_err:
            print(f"⚠️ [Step 2 Error] Could not fetch language: {lang_err}")
            traceback.print_exc()
            owner_lang = "fa"

        try:
            print("🈳 [Step 3] Translating 'out_of_stock' text...")
            out_of_stock_text = await t(owner_lang, "out_of_stock")
            print(f"✅ [Step 3] Translated text: {out_of_stock_text}")
        except Exception as t_err:
            print(f"⚠️ [Step 3 Error] Translation failed: {t_err}")
            traceback.print_exc()
            out_of_stock_text = "اتمام موجودی"

        # --- 3. ارسال پیام با TeleBot ---
        try:
            print("📤 [Step 4] Sending ❌ out-of-stock message via TeleBot...")
            bot.send_message(channel_id, f"❌ {out_of_stock_text}")
            print("✅ [Step 4] Out-of-stock message sent successfully!")
        except Exception as bot_err:
            print(f"❌ [Step 4 Error] Failed to send message via TeleBot: {bot_err}")
            traceback.print_exc()

        await client.disconnect()
        print("🔚 [Telethon] Client disconnected.\n")

    except Exception as e:
        print("❌ [send_out_of_stock_announcement] Unhandled error:", e)
        traceback.print_exc()



# 🟢 تابع امن برای اجرای تابع بالا در محیط sync یا async
def send_out_of_stock_sync(channel_id, product, photos):
    """
    اجرای امن تابع async در هر محیطی (حتی اگر event loop فعال باشد)
    """
    print(f"\n⚙️ [send_out_of_stock_sync] Running for {product.name}")
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            print("🔄 Event loop already running → creating background task.")
            asyncio.ensure_future(send_out_of_stock_announcement(channel_id, product, photos))
        else:
            print("🚀 Starting new event loop for out-of-stock task...")
            loop.run_until_complete(send_out_of_stock_announcement(channel_id, product, photos))
    except RuntimeError:
        print("🆕 No running event loop found → creating new one.")
        asyncio.run(send_out_of_stock_announcement(channel_id, product, photos))
    except Exception as e:
        print("⚠️ [send_out_of_stock_sync] Error while running async function:", e)
        traceback.print_exc()



# 🧩 تابع اصلی پردازش پرداخت موفق
def handle_successful_payment(transaction):
    try:
        if transaction.status == "paid" and transaction.cart:
            print("\n==================== 💳 PAYMENT PROCESS STARTED ====================")
            print(f"Transaction ID: {transaction.id}, Buyer: {transaction.profile.tel_id}")

            sales = []
            for cart_item in transaction.cart.items.all():
                product = cart_item.product
                print(f"\n🔹 Checking product: {product.name} | Stock: {product.stock} | Quantity: {cart_item.quantity}")

                if product.stock >= cart_item.quantity:
                    # کاهش موجودی
                    product.stock -= cart_item.quantity
                    product.save(update_fields=["stock"])
                    print(f"✅ Stock updated → New stock: {product.stock}")

                    # ثبت فروش
                    sale = Sale.objects.create(
                        transaction=transaction,
                        product=product,
                        seller=product.store,
                        quantity=cart_item.quantity,
                        unit_price=product.final_price,
                        total_price=cart_item.total_price()
                    )
                    sales.append(sale)
                    print(f"🧾 Sale created: {sale.product.name} x {sale.quantity} ({sale.total_price})")

                    # 🛑 اگر موجودی صفر شد
                    if product.stock == 0 and product.store.tel_channel:
                        print(f"📢 Product '{product.name}' is now OUT OF STOCK! Sending notification...")
                        try:
                            photos = []
                            if product.main_image:
                                photos.append(product.main_image.path)
                            photos += [img.image.path for img in product.images.all()]

                            send_out_of_stock_sync(
                                channel_id=product.store.tel_channel,
                                product=product,
                                photos=photos
                            )
                        except Exception as ex:
                            print(f"⚠️ Error sending out-of-stock message for {product.name}: {ex}")
                            traceback.print_exc()

                else:
                    print(f"⚠️ Not enough stock for {product.name}, removing from cart...")
                    cart_item.delete()
                    continue

            if not sales:
                print("⚠️ No valid sales created due to insufficient stock.")
                return

            # پیام به خریدار
            chat_id_buyer = transaction.profile.tel_id
            telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            buyer_products = "\n".join(
                [f"🔹 {s.product.name} × {s.quantity} = {s.total_price} تومان" for s in sales]
            )
            buyer_message = (
                "✅ پرداخت شما با موفقیت انجام شد!\n"
                f"🛍️ محصولات خریداری‌شده:\n{buyer_products}\n\n"
                f"💰 مبلغ کل: {transaction.amount} تومان"
            )
            print(f"📩 Sending confirmation to buyer {chat_id_buyer}...")
            buyer_res = requests.post(telegram_url, json={"chat_id": chat_id_buyer, "text": buyer_message})
            print(f"📩 Buyer response: {buyer_res.status_code} | {buyer_res.text}")

            # پیام به فروشندگان
            sellers_map = {}
            for s in sales:
                seller_tel_id = s.seller.owner.tel_id
                print(f"🔎 Preparing seller notification: {seller_tel_id}")
                if not seller_tel_id:
                    print(f"⚠️ Seller {s.seller.name} has no tel_id, skipping.")
                    continue
                if seller_tel_id not in sellers_map:
                    sellers_map[seller_tel_id] = {
                        "store": s.seller,
                        "products": [],
                        "total_income": 0,
                    }
                sellers_map[seller_tel_id]["products"].append(s)
                sellers_map[seller_tel_id]["total_income"] += s.total_price

            buyer_fname = transaction.profile.fname or ""
            buyer_lname = transaction.profile.lname or ""
            buyer_phone = transaction.profile.phone or ""
            buyer_address = transaction.profile.get_active_address()
            address_text = ""
            if buyer_address:
                address_text = (
                    f"{buyer_address.shipping_line1}, "
                    f"{buyer_address.shipping_city}, "
                    f"{buyer_address.shipping_province}, "
                    f"{buyer_address.shipping_country}"
                )

            for chat_id_seller, data in sellers_map.items():
                seller_products = "\n".join(
                    [f"🔹 {s.product.code} | {s.product.name} × {s.quantity} = {s.total_price} تومان"
                     for s in data["products"]]
                )
                seller_message = (
                    f"📦 سفارش جدید در فروشگاه {data['store'].name}\n\n"
                    f"{seller_products}\n\n"
                    f"💰 مجموع درآمد شما: {data['total_income']} تومان\n\n"
                    f"👤 خریدار: {buyer_fname} {buyer_lname}\n"
                    f"📞 تلفن: {buyer_phone}\n"
                    f"🏠 آدرس: {address_text if address_text else 'نامشخص'}"
                )
                print(f"📩 Sending message to seller {chat_id_seller}...")
                seller_res = requests.post(telegram_url, json={"chat_id": chat_id_seller, "text": seller_message})
                print(f"📩 Seller response: {seller_res.status_code} | {seller_res.text}")

            transaction.cart.items.all().delete()
            print("🛒 Cart cleared successfully.")
            print("==================== ✅ PAYMENT PROCESS COMPLETED ====================\n")

    except Exception as e:
        print(f"❌ [handle_successful_payment] Error: {e}")
        traceback.print_exc()
