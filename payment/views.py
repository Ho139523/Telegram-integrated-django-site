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
from AI.settings import SITE_DOMAIN
from telbot.sessions import SessionManager
from dotenv import load_dotenv
import os

# 🧩 مدل‌ها و پکیج‌های پروژه
from .zarinpal import ZarinPal
from products.models import Product
from accounts.models import ProfileModel
from payment.models import Transaction, Sale, Cart, CartItem
from utils.variables.TOKEN import TOKEN, api_id, api_hash, BOT_ID
from products.signals import helper
from utils.telbot.functions import ProductHandler, t
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

def request_restock(channel_id, product, photos, attributes):
    """ارسال آلبوم محصول با کپشن مشابه ProductHandler و دکمه خرید یا درخواست موجود کردن"""
    print(f"\n🚀 [send_album_and_button_async] Sending product {product.name}")
    try:
        owner_lang, store_id, product_id, chat_id = helper(product)
        handler = ProductHandler(bot, product, SITE_DOMAIN, photos=photos, attributes=attributes, chat_id=chat_id)
        handler.send_product_message(channel_id, buttons=False, out_of_stock=True)

        # 🧩 ساخت دکمه
        markup = types.InlineKeyboardMarkup()
        owner_lang, store_id, product_id, chat_id = helper(product)

        #ترجمه‌ی متن دکمه ---
        request_product_text = t("message", "request_restock", lang=owner_lang)
        markup.add(types.InlineKeyboardButton(request_product_text, callback_data=f"request_{product.id}"))
        

        # ارسال دکمه با ربات
        bot.send_message(channel_id, "👇👇👇👇👇👇👇👇👇", reply_markup=markup)

        print("✅ [send_album_and_button_async] Message sent successfully.\n")

    except Exception as e:
        print(f"❌ Error in send_album_and_button_async: {traceback.format_exc()}")



# ==========================================================
# 💳 درخواست پرداخت
# ==========================================================
from django.core.cache import cache
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
import traceback


def send_request(request):

    if request.method != "GET":
        return JsonResponse(
            {"error": "Method not allowed"},
            status=405
        )

    try:

        payment_id = request.GET.get("pid")

        if not payment_id:
            return JsonResponse(
                {"error": "شناسه پرداخت نامعتبر است"},
                status=400
            )

        print(f"Payment ID: {payment_id}")

        payment_data = cache.get(f"payment_{payment_id}")

        if not payment_data:
            return JsonResponse(
                {"error": "لینک پرداخت منقضی شده است"},
                status=400
            )

        tel_id = payment_data["tel_id"]

        profile = ProfileModel.objects.get(
            tel_id=tel_id
        )

        cart = Cart.objects.get(
            profile=profile
        )

        cart_items = CartItem.objects.filter(
            cart=cart
        )

        if not cart_items.exists():
            return JsonResponse(
                {"error": "سبد خرید خالی است"},
                status=400
            )

        # مبلغ کل (ریال)
        amount = int(
            sum(
                item.total_price()
                for item in cart_items
            ) * 10
        )

        # -----------------------------
        # ساخت wages برای زرین پال
        # -----------------------------
        splits = []

        sellers_split = cart.get_sellers_split()

        if len(sellers_split) > 5:

            return JsonResponse(
                {
                    "error":
                    "حداکثر ۵ فروشنده در یک تراکنش پشتیبانی می‌شود."
                },
                status=400
            )

        total_split_amount = 0

        for seller, seller_amount in sellers_split.items():

            if not seller.iban:

                return JsonResponse(
                    {
                        "error":
                        f"فروشگاه «{seller.name}» شماره شبا ثبت نکرده است."
                    },
                    status=400
                )

            seller_amount_rial = int(
                seller_amount * 10
            )

            total_split_amount += seller_amount_rial

            splits.append({
                "iban": seller.iban,
                "amount": seller_amount_rial,
                "description":
                    f"سهم فروشگاه {seller.name}"
            })

        # طبق محدودیت زرین پال
        # فقط اگر سهم فروشندگان از مبلغ کل بیشتر شد خطا بده
        if total_split_amount > amount:
        
            return JsonResponse(
                {
                    "error":
                    "مجموع سهم فروشندگان نباید بیشتر از مبلغ کل باشد."
                },
                status=400
            )

        description = (
            f"پرداخت سبد خرید شامل "
            f"{cart_items.count()} کالا"
        )

        response = pay.send_split_request(
            amount=amount,
            description=description,
            splits=splits,
            email=None,
            mobile=profile.phone
        )

        if not response.get("success"):

            return JsonResponse(
                {
                    "error":
                    response.get(
                        "message",
                        "خطا در اتصال به درگاه"
                    ),
                    "code":
                    response.get(
                        "error_code"
                    )
                },
                status=400
            )

        authority = response.get(
            "authority"
        )

        if not authority:

            return JsonResponse(
                {
                    "error":
                    "Authority دریافت نشد"
                },
                status=400
            )

        transaction = Transaction.objects.create(
            profile=profile,
            cart=cart,
            amount=amount // 10,   # تومان
            authority=authority,
            status="pending"
        )

        transaction.create_split_payments()

        cache.delete(
            f"payment_{payment_id}"
        )

        payment_url = response["url"]

        print("=" * 60)
        print("PAYMENT URL:")
        print(payment_url)
        print("=" * 60)

        html = f"""
        <!DOCTYPE html>
        <html lang="fa">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport"
                content="width=device-width, initial-scale=1.0">
            <title>انتقال به درگاه پرداخت</title>

            <style>
                body {{
                    font-family: sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: #f5f5f5;
                    direction: rtl;
                }}

                .card {{
                    background: white;
                    padding: 30px;
                    border-radius: 16px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                    text-align: center;
                    max-width: 400px;
                }}

                .btn {{
                    display: inline-block;
                    margin-top: 20px;
                    padding: 12px 24px;
                    background: #0088cc;
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                }}
            </style>
        </head>

        <body>

        <div class="card">
            <h3>در حال انتقال به درگاه پرداخت...</h3>

            <p>
                اگر انتقال خودکار انجام نشد،
                روی دکمه زیر کلیک کنید.
            </p>

            <a class="btn"
            href="{payment_url}"
            target="_blank">
                ورود به درگاه پرداخت
            </a>
        </div>

        <script>

        const paymentUrl = "{payment_url}";

        if (
            window.Telegram &&
            Telegram.WebApp &&
            Telegram.WebApp.openLink
        ) {{

            Telegram.WebApp.openLink(
                paymentUrl,
                {{
                    try_instant_view: false
                }}
            );

            setTimeout(() => {{
                Telegram.WebApp.close();
            }}, 500);

        }} else {{

            window.location.replace(paymentUrl);

        }}

        </script>

        </body>
        </html>
        """

        return HttpResponse(html)

    except ProfileModel.DoesNotExist:

        return JsonResponse(
            {
                "error":
                "پروفایل یافت نشد"
            },
            status=404
        )

    except Cart.DoesNotExist:

        return JsonResponse(
            {
                "error":
                "سبد خرید یافت نشد"
            },
            status=404
        )

    except Exception:

        print(
            traceback.format_exc()
        )

        return JsonResponse(
            {
                "error":
                traceback.format_exc()
            },
            status=500
        )


# ==========================================================
# ✅ تایید پرداخت موفق
# ==========================================================
@csrf_exempt
def verify(request):
    try:

        authority = request.GET.get("Authority")
        status = request.GET.get("Status")

        if not authority:
            return JsonResponse(
                {"error": "Missing authority"},
                status=400
            )

        try:
            transaction = Transaction.objects.get(
                authority=authority
            )

        except Transaction.DoesNotExist:

            return JsonResponse(
                {"error": "Transaction not found"},
                status=404
            )

        # جلوگیری از پردازش مجدد callback
        if transaction.status == "paid":

            return render(
                request,
                "payment/tel_payment_success.html",
                {
                    "message": "این پرداخت قبلاً ثبت شده است."
                }
            )

        # کاربر پرداخت را لغو کرده است
        if status != "OK":

            transaction.mark_as_canceled()

            return render(
                request,
                "payment/tel_payment_failed.html",
                {
                    "message": "پرداخت لغو شد."
                }
            )

        # تایید پرداخت نزد زرین پال
        response = pay.verify(
            authority=authority,
            amount=transaction.amount * 10
        )

        print("VERIFY RESPONSE:")
        print(response)

        # پرداخت موفق
        if response.get("success"):

            transaction.status = "paid"
            transaction.zarinpal_ref_id = response.get("ref_id")

            transaction.save(
                update_fields=[
                    "status",
                    "zarinpal_ref_id"
                ]
            )

            try:

                # ایجاد سفارش، ثبت فروش‌ها،
                # خالی کردن سبد و کم کردن موجودی
                handle_successful_payment(transaction)

                # پاک کردن سشن سبد خرید تلگرام
                session_manager = SessionManager()

                session_manager.reset_user_session(
                    transaction.profile.tel_id,
                    namespace="cart"
                )

            except Exception as e:

                print(
                    f"❌ Error in "
                    f"handle_successful_payment: {e}"
                )

                transaction.mark_as_failed()

                return render(
                    request,
                    "payment/tel_payment_failed.html",
                    {
                        "message":
                            f"خطا در ثبت سفارش: {str(e)}"
                    }
                )

            return render(
                request,
                "payment/tel_payment_success.html",
                {
                    "ref_id": response.get("ref_id"),
                    "message": "پرداخت با موفقیت انجام شد."
                }
            )

        # تایید زرین پال ناموفق بود
        transaction.mark_as_failed()

        return render(
            request,
            "payment/tel_payment_failed.html",
            {
                "message":
                    response.get(
                        "message",
                        "خطای ناشناخته در تایید پرداخت"
                    )
            }
        )

    except Exception as e:

        print(f"❌ Verify Error: {e}")

        return JsonResponse(
            {"error": str(e)},
            status=500
        )

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
                        
                        request_restock(
                            channel_id=product.store.tel_channel,
                            product=product,
                            photos=photos,
                            attributes=list(product.attributes.all()),
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
        from sms_ir import SmsIr
        SmsIrsms_ir = SmsIr(str(os.environ.get('sms_api_key')), str(os.environ.get('linenumber')))
        
        # پیام به خریدار
        buyer_products = "\n".join(
            [f"🔹 {s.product.name} × {s.quantity} = {s.total_price:,} تومان" for s in sales]
        )
        buyer_message = (
            "✅ پرداخت شما با موفقیت انجام شد!\n"
            f"🛍️ محصولات خریداری‌شده:\n{buyer_products}\n\n"
            f"💰 مبلغ کل: {transaction.amount:,} تومان\n"
            f"📋 کد پیگیری زرین پال: {transaction.zarinpal_ref_id or '---'}"
        )
        print(str(transaction.profile.phone))
        print(str(os.environ.get('linenumber')))
        sms = SmsIrsms_ir.send_sms(str(transaction.profile.phone), buyer_message, str(os.environ.get('linenumber')))
        print(sms.json())
        msg = bot.send_message(chat_id=chat_id_buyer, text=buyer_message)

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
                f"🏠 آدرس: {address_text}\n\n"
                f"کد تراکنش: {transaction.transaction_id}"
            )

            SmsIrsms_ir.send_sms(str(data["store"].owner.phone), seller_message, str(os.environ.get('linenumber')))
            bot.send_message(chat_id=chat_id_seller, text=seller_message)
    except Exception as e:
        print(f"❌ Error sending notifications: {traceback.format_exc()}")




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
        lang = urllib.parse.quote(start_param)
        lang = lang.split("_")
        lang = lang[-1]
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
                    <h3 style="color: red">{t("message", "VPN_required", lang=lang)}</h3>
                    
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
                            window.location.href = 'https://intelleum.ir';
                        }}, 30000);
                        
                    </script>
                    
                    <p style="margin-top:30px; color:#666; font-size:14px;">
                        در صورت عدم انتقال خودکار:
                        <br>
                        <a href="{telegram_url}" style="display:inline-block; margin-top:10px; padding:8px 16px; background:#0088cc; color:white; text-decoration:none; border-radius:5px;">
                            🔗 باز کردن ربات
                        </a>
                        <br>
                        <a href="https://intelleum.ir" style="display:inline-block; margin-top:10px; padding:8px 16px; background:#28a745; color:white; text-decoration:none; border-radius:5px;">
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
