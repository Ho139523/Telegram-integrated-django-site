from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .zarinpal import ZarinPal
import json
from products.models import Product
from accounts.models import ProfileModel
from payment.models import Transaction, Sale, Cart, CartItem
import requests
from utils.variables.TOKEN import TOKEN
from django.shortcuts import render
import base64
import traceback
from django.http import HttpResponseRedirect

pay = ZarinPal()

@csrf_exempt
def send_request(request):
    if request.method == "GET":
        try:
            # دریافت داده‌های JSON از body
            # data = json.loads(request.body)
            encoded_data = request.GET.get('data')
            decoded_data = base64.b64decode(encoded_data).decode()
            data = json.loads(decoded_data)
            tel_id = data['tel_id']
            # استخراج اطلاعات محصول و کاربر
            # tel_id = data.get("tel_id", {})
            # message_data = data.get("message", {})
            # chat_id = message_data.get("chat_id")
            # product_code = product_data.get("code")
            # return JsonResponse({"error": f"tel_id is : {tel_id}"}, status=400)
            profile = ProfileModel.objects.get(tel_id=tel_id)
            cart = Cart.objects.get(profile=profile)
            cart_items = CartItem.objects.filter(cart=cart)

            if not cart_items.exists():
                return JsonResponse({"error": "سبد خرید خالی است"}, status=400)
            
            amount = sum(item.total_price() for item in cart_items)
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



def handle_successful_payment(transaction):
    try:
        if transaction.status == "paid" and transaction.cart:
            # حذف بررسی وجود قبلی Sale چون برای هر محصول یک رکورد جدید ایجاد می‌کنیم
            for cart_item in transaction.cart.items.all():
                Sale.objects.create(
                    transaction=transaction,
                    product=cart_item.product,
                    seller=cart_item.product.store,
                    quantity=cart_item.quantity,
                    unit_price=cart_item.product.final_price,
                    total_price=cart_item.total_price()
                )
            
            # ارسال پیام به تلگرام
            chat_id = transaction.profile.tel_id
            telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            message = f"✅ پرداخت شما با موفقیت انجام شد!\n🔹 مبلغ کل: {transaction.amount} تومان"
            requests.post(telegram_url, json={"chat_id": chat_id, "text": message})
            
            # خالی کردن سبد خرید پس از پرداخت موفق
            transaction.cart.items.all().delete()

    except Exception as e:
        print(f"Error in processing successful payment: {e}")
