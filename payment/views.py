import  attrs
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
from telbot.sessions import SessionManager

# 🧩 مدل‌ها و پکیج‌های پروژه
from .zarinpal import ZarinPal
from products.models import Product
from accounts.models import ProfileModel
from payment.models import Transaction, Sale, Cart, CartItem
from utils.variables.TOKEN import TOKEN, api_id, api_hash, BOT_ID
from products.signals import t, async_helper
from django.db import transaction as db_transaction
from django.db import models

# 🟩 تنظیمات عمومی
pay = ZarinPal()
bot = TeleBot(TOKEN)
SESSION_STRING = settings.TG_SESSION_STRING
API_ID = api_id
API_HASH = api_hash


# ==========================================================
# 🧩 تابع ارسال آلبوم محصول (با حالت اتمام موجودی یا معمولی)
# ==========================================================

from collections import defaultdict
from asgiref.sync import sync_to_async


async def async_get_variants_text(product):
    variants = await sync_to_async(list)(
        product.variants.all()
    )

    variants_dict = defaultdict(set)

    for variant in variants:
        options = await sync_to_async(list)(
            variant.values.select_related("option").all()
        )
        for opt in options:
            variants_dict[opt.option.name].add(opt.value)

    if not variants_dict:
        return ""

    lines = [
        f"✅ {key}: {', '.join(values)}"
        for key, values in variants_dict.items()
    ]

    return "\n".join(lines) + "\n\n"

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
            attribute_text = "\n✨ ".join(
                [f"{attr.key}: {attr.value}" if attr.value else f"{attr.key}" for attr in attributes]
            )
            attribute_text = f"✨ {attribute_text}\n\n"

        variants_text = await async_get_variants_text(product)

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
            f"{variants_text}"
            f"{price_text}\n"
        )


        # 🧩 ساخت دکمه
        markup = types.InlineKeyboardMarkup()
        owner_lang, store_id, product_id, chat_id = await async_helper(product)

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
            session_manager = SessionManager()
            session_manager.reset_user_session(transaction.profile.tel_id, namespace="cart")
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
        print("1. شروع پردازش تراکنش")
        if transaction.status != "paid" or not transaction.cart:
            print("❌ تراکنش paid نیست یا سبد خرید ندارد")
            return
        print(f"2. پردازش تراکنش: {transaction.id}")

        out_of_stock_products = set()
        print("3. شروع تراکنش دیتابیس")
        
        with db_transaction.atomic():
            sales = []
            cart_items = list(transaction.cart.items.select_related("product", "variant"))

            print(f"4. تعداد آیتم‌های سبد خرید: {len(cart_items)}")
            
            for index, cart_item in enumerate(cart_items):
                product = cart_item.product
                quantity = cart_item.quantity
                print(f"\n{'='*50}")
                print(f"آیتم {index + 1}: {product.name} (ID: {product.id})")
                print(f"تعداد: {quantity}")
                
                # 🔥 بررسی مستقیم از دیتابیس برای اطمینان
                from payment.models import ProductVariant
                actual_has_variants = ProductVariant.objects.filter(product=product).exists()
                print(f"has_variants() نتیجه: {product.has_variants()}")
                print(f"بررسی مستقیم دیتابیس: {actual_has_variants}")
                print(f"واریانت در cart_item: {cart_item.variant}")
                print(f"تعداد واریانت‌ها در دیتابیس: {product.get_active_variants_count()}")
                
                variant = cart_item.variant
                
                # ===============================
                # 🧩 منطق اصلی با قابلیت انتخاب خودکار واریانت
                # ===============================
                
                # اگر در دیتابیس واقعاً واریانت دارد
                if actual_has_variants:
                    print("5. محصول در دیتابیس واریانت دارد")
                    
                    # اگر واریانت انتخاب نشده، سعی کن یکی انتخاب کنی
                    if not variant:
                        print("⚠️ واریانت انتخاب نشده - جستجوی واریانت مناسب")
                        
                        # گزینه 1: اولین واریانت با موجودی کافی
                        available_variants = product.variants.filter(stock__gte=quantity)
                        
                        if available_variants.exists():
                            variant = available_variants.first()
                            print(f"   ✅ واریانت پیدا شد: {variant} (موجودی: {variant.stock})")
                            
                            # آپدیت cart_item با واریانت پیدا شده
                            cart_item.variant = variant
                            cart_item.save(update_fields=["variant"])
                            print(f"   CartItem آپدیت شد با واریانت ID: {variant.id}")
                        else:
                            # گزینه 2: اولین واریانت موجود
                            first_variant = product.variants.first()
                            if first_variant:
                                print(f"   ⚠️ واریانت با موجودی کافی یافت نشد، استفاده از اولین واریانت: {first_variant}")
                                print(f"   موجودی واریانت: {first_variant.stock}, درخواست: {quantity}")
                                
                                if first_variant.stock < quantity:
                                    error_msg = f"موجودی واریانت '{first_variant}' کافی نیست (موجودی: {first_variant.stock}, درخواست: {quantity})"
                                    print(f"❌ {error_msg}")
                                    raise ValueError(error_msg)
                                
                                variant = first_variant
                                cart_item.variant = variant
                                cart_item.save(update_fields=["variant"])
                                print(f"   CartItem آپدیت شد با واریانت ID: {variant.id}")
                            else:
                                error_msg = f"هیچ واریانتی برای محصول '{product.name}' یافت نشد!"
                                print(f"❌ {error_msg}")
                                raise ValueError(error_msg)
                    
                    # اکنون variant حتماً مقدار دارد
                    print(f"6. پردازش واریانت: {variant} (ID: {variant.id})")
                    print(f"   موجودی واریانت قبل: {variant.stock}")
                    
                    if variant.stock < quantity:
                        error_msg = f"موجودی واریانت {variant} کافی نیست (موجودی: {variant.stock}, درخواست: {quantity})"
                        print(f"❌ {error_msg}")
                        raise ValueError(error_msg)
                    
                    # کاهش موجودی واریانت
                    variant.stock -= quantity
                    variant.save()
                    print(f"7. واریانت ذخیره شد - موجودی بعد: {variant.stock}")
                    
                    # sync موجودی محصول اصلی
                    print("8. شروع sync موجودی محصول اصلی")
                    product.refresh_from_db(fields=["stock"])
                    print(f"   موجودی محصول قبل از sync: {product.stock}")
                    
                    # استفاده از system_update=True در save
                    product.save(system_update=True)
                    
                    print(f"   موجودی محصول بعد از sync: {product.stock}")
                    
                    # ایجاد رکورد فروش
                    sale = Sale.objects.create(
                        transaction=transaction,
                        product=product,
                        seller=product.store,
                        quantity=quantity,
                        unit_price=int(variant.final_price),
                        total_price=int(cart_item.total_price()),
                    )
                    sales.append(sale)
                    print(f"9. فروش ثبت شد - Sale ID: {sale.id}")
                
                else:
                    print("10. محصول واقعاً بدون واریانت است")
                    
                    print(f"   موجودی محصول قبل: {product.stock}")
                    
                    if product.stock < quantity:
                        error_msg = f"موجودی محصول {product} کافی نیست (موجودی: {product.stock}, درخواست: {quantity})"
                        print(f"❌ {error_msg}")
                        raise ValueError(error_msg)
                    
                    # کاهش موجودی محصول
                    product.stock -= quantity
                    product.save(system_update=True)
                    
                    print(f"   موجودی محصول بعد: {product.stock}")
                    print("12. محصول ذخیره شد")
                    
                    # ایجاد رکورد فروش
                    sale = Sale.objects.create(
                        transaction=transaction,
                        product=product,
                        seller=product.store,
                        quantity=quantity,
                        unit_price=int(product.final_price),
                        total_price=int(cart_item.total_price()),
                    )
                    sales.append(sale)
                    print(f"13. فروش ثبت شد - Sale ID: {sale.id}")
                
                # ===============================
                # 📣 OUT OF STOCK NOTIFICATION
                # ===============================
                print("14. بررسی اتمام موجودی")
                product.refresh_from_db()
                print(f"   محصول: {product.name}")
                print(f"   موجودی در دیتابیس: {product.stock}")
                
                # بررسی موجودی صفر
                stock_to_check = product.stock
                if actual_has_variants:
                    total_variant_stock = product.variants.aggregate(total=models.Sum("stock"))["total"] or 0
                    stock_to_check = total_variant_stock
                    print(f"   مجموع موجودی واریانت‌ها: {total_variant_stock}")
                
                print(f"   موجودی برای بررسی: {stock_to_check}")
                
                if (
                    stock_to_check == 0
                    and product.store.tel_channel
                    and product.id not in out_of_stock_products
                ):
                    print("15. محصول تمام شده است - ارسال اعلان")
                    out_of_stock_products.add(product.id)

                    photos = []
                    if product.main_image:
                        photos.append(product.main_image.path)
                        print(f"   تصویر اصلی: {product.main_image.path}")
                    
                    product_images = [img.image.path for img in product.images.all()]
                    photos += product_images
                    print(f"   تعداد تصاویر اضافی: {len(product_images)}")

                    try:
                        print("16. ارسال آلبوم به کانال")
                        print(f"   کانال: {product.store.tel_channel}")
                        print(f"   محصول: {product.name}")
                        
                        send_album_and_button(
                            channel_id=product.store.tel_channel,
                            product=product,
                            photos=photos,
                            out_of_stock=True,
                        )
                        print("17. آلبوم ارسال شد")
                    except Exception as ex:
                        print(f"⚠️ خطا در ارسال آلبوم اتمام موجودی: {ex}")
                        traceback.print_exc()

            print(f"\n{'='*50}")
            print("پردازش تمام آیتم‌ها تکمیل شد")
            
            print("ارسال نوتیفیکیشن‌ها...")
            send_payment_notifications(transaction, sales)

            print("پاک کردن سبد خرید...")
            transaction.cart.items.all().delete()
            print("✅ پردازش تراکنش با موفقیت کامل شد")

    except Exception as e:
        print(f"\n❌❌❌ خطا در handle_successful_payment: {e}")
        print(f"❌ تراکنش: {transaction.id if transaction else 'N/A'}")
        traceback.print_exc()
        raise




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




################ SERIALISERS ##################

from rest_framework import viewsets, permissions
from .models import Cart, CartItem, Transaction, SplitPayment, Sale
from .serializers import CartSerializer, CartItemSerializer, TransactionSerializer, SplitPaymentSerializer, SaleSerializer
from rest_framework.permissions import IsAuthenticated


class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]  # فقط کاربران واردشده

    def get_queryset(self):
        # فقط کارت‌های کاربر جاری
        user = self.request.user
        try:
            profile = user.profilemodel
            return Cart.objects.filter(profile=profile)
        except ProfileModel.DoesNotExist:
            return Cart.objects.none()

    def perform_create(self, serializer):
        profile = self.request.user.profilemodel
        serializer.save(profile=profile)


class CartItemViewSet(viewsets.ModelViewSet):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]  # فقط کاربران واردشده

    def get_queryset(self):
        user = self.request.user
        try:
            profile = user.profilemodel
            return Transaction.objects.filter(profile=profile)
        except ProfileModel.DoesNotExist:
            return Transaction.objects.none()

    def perform_create(self, serializer):
        profile = self.request.user.profilemodel
        serializer.save(profile=profile)



class SplitPaymentViewSet(viewsets.ModelViewSet):
    queryset = SplitPayment.objects.all()
    serializer_class = SplitPaymentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


@csrf_exempt
def refund_payment(request, transaction_id):
    txn = Transaction.objects.get(id=transaction_id)
    txn.refund()
    return JsonResponse({"message": "تراکنش مرجوع شد"})


#############################  ASYNCE PAYMENT #############################

import redis.asyncio as aioredis
import httpx
from asgiref.sync import sync_to_async
from django.http import JsonResponse
from payment.models import Transaction

REDIS_URL = "redis://localhost"

async def async_verify_payment(request):
    authority = request.GET.get("Authority")
    status = request.GET.get("Status")

    if not authority:
        return JsonResponse({"error": "Missing authority"}, status=400)

    try:
        transaction = await sync_to_async(Transaction.objects.get)(authority=authority)
    except Transaction.DoesNotExist:
        return JsonResponse({"error": "Transaction not found"}, status=404)

    if status != "OK":
        await sync_to_async(transaction.mark_as_canceled)()
        return JsonResponse({"message": "پرداخت لغو شد"})

    # Async verify via httpx
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://www.zarinpal.com/pg/rest/WebGate/PaymentVerification.json",
            json={"Authority": authority, "Amount": transaction.amount * 10}
        )
        data = await resp.json()

    if data.get("Status") != 100:
        await sync_to_async(transaction.mark_as_failed)()
        return JsonResponse({"error": "پرداخت ناموفق"})

    # Redis lock
    redis = await aioredis.from_url(REDIS_URL)
    lock_key = f"transaction_lock:{transaction.id}"
    lock = redis.lock(lock_key, timeout=30)
    acquired = await lock.acquire()
    if not acquired:
        await redis.close()
        return JsonResponse({"error": "تراکنش در حال پردازش است"})

    try:
        # اجرای finalize با atomic و lock
        await sync_to_async(transaction.finalize)()
    finally:
        await lock.release()
        await redis.close()

    return JsonResponse({"message": "پرداخت موفق و finalize شد", "ref_id": data.get("RefID")})
   




from django.shortcuts import redirect
from django.views import View
from django.conf import settings
import urllib.parse
from utils.variables.TOKEN import BOT_ID

from django.http import HttpResponse
from django.urls import reverse

class TelegramBotRedirectView(View):
    def get(self, request):
        start_param = request.GET.get('start', '')
        
        if not start_param:
            return redirect('mainpage:home')
        
        bot_id = BOT_ID  # یا از settings بیاورید
        
        if not bot_id:
            return redirect('error_page')
        
        telegram_url = f"https://t.me/{bot_id}?start={urllib.parse.quote(start_param)}"
        home_url = reverse('mainpage:home')
        
        # HTML با JavaScript برای باز کردن تلگرام در پس‌زمینه
        html_content = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>اتصال به ربات</title>
                <script src="https://telegram.org/js/telegram-web-app.js"></script>
            </head>
            <body>
                <div style="text-align:center; padding:20px;">
                    <h2>در حال انتقال به ربات...</h2>
                    
                    <script>
                        // بررسی اگر در WebView تلگرام هستیم
                        if (window.Telegram && Telegram.WebApp) {{
                            const tg = Telegram.WebApp;
                            
                            // تلاش برای باز کردن ربات از طریق Telegram WebApp
                            try {{
                                tg.openTelegramLink('{telegram_url}');
                            }} catch (error) {{
                                tg.openLink('{telegram_url}');
                            }}
                            
                        }} else {{
                            // اگر در WebView تلگرام نیستیم، روش عادی
                            window.location.href = '{telegram_url}';
                        }}
                        
                        // ===== مهم: بعد از 3 ثانیه صفحه را به سایت اصلی منتقل کن =====
                        setTimeout(function() {{
                            // این خط صفحه فعلی را به آدرس سایت اصلی منتقل می‌کند
                            window.location.href = 'https://intelleum.ir:8443';
                        }}, 3000);
                        
                    </script>
                    
                    <p style="margin-top:30px; color:#666; font-size:14px;">
                        در صورت عدم انتقال خودکار:
                        <br>
                        <a href="{telegram_url}" style="display:inline-block; margin-top:10px; padding:8px 16px; background:#0088cc; color:white; text-decoration:none; border-radius:5px;">
                            🔗 باز کردن ربات
                        </a>
                        <br>
                        <a href="https://intelleum.ir:8443" style="display:inline-block; margin-top:10px; padding:8px 16px; background:#28a745; color:white; text-decoration:none; border-radius:5px;">
                            🏠 رفتن به سایت اصلی
                        </a>
                    </p>
                    
                    <div style="margin-top:40px; font-size:12px; color:#999;">
                        انتقال خودکار به سایت اصلی در <span id="countdown">3</span> ثانیه
                    </div>
                    
                    <script>
                        // شمارش معکوس نمایشی
                        let seconds = 3;
                        const countdownElement = document.getElementById('countdown');
                        const countdownInterval = setInterval(function() {{
                            seconds--;
                            countdownElement.textContent = seconds;
                            if (seconds <= 0) {{
                                clearInterval(countdownInterval);
                            }}
                        }}, 1000);
                    </script>
                </div>
            </body>
            </html>
            '''
        return HttpResponse(html_content)
