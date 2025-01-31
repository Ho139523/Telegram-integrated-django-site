from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .zarinpal import ZarinPal
import json
from products.models import Product
from accounts.models import ProfileModel
from payment.models import Transaction
import requests
from utils.variables.TOKEN import TOKEN

pay = ZarinPal()

@csrf_exempt
def send_request(request):
    try:
        if request.method == "POST":
            try:
                # دریافت داده‌های JSON از body
                data = json.loads(request.body)

                # استخراج اطلاعات محصول و کاربر
                product_data = data.get("data", {})
                message_data = data.get("message", {})
                chat_id = message_data.get("chat_id")
                product_code = product_data.get("code")

                if not product_code:
                    return JsonResponse({"error": "Product code is required"}, status=400)

                # دریافت اطلاعات کالا
                amount = int(float(product_data.get("final_price", "0"))) * 10  # تبدیل به ریال
                description = f"{product_data.get('name')} - {product_data.get('description')}"  # توضیحات

                # ارسال درخواست پرداخت به زرین‌پال
                response = pay.send_request(
                    amount=amount,
                    description=description,
                    email="admin@admin.com",
                    mobile=str("09123456789")  # تبدیل مقدار به رشته
                )


                # 🚀 لاگ پاسخ دریافتی از زرین‌پال
                print(f"ZarinPal Response: {response}")

                authority = response.get("authority")
                if not authority:
                    return JsonResponse({"error": "Failed to get authority from ZarinPal"}, status=400)

                # ایجاد تراکنش در دیتابیس
                transaction = Transaction.objects.create(
                    profile=ProfileModel.objects.get(tel_id=chat_id),
                    product=Product.objects.get(code=product_code),
                    amount=amount // 10,  # مقدار به تومان
                    authority=authority,
                    status="pending"
                )
                
                return JsonResponse({"redirect_url": response["url"]})

            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid JSON"}, status=400)
        else:
            return JsonResponse({"error": "Invalid method"}, status=405)

    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({"error": f"An internal error occurred. {str(e)}"}, status=500)


@csrf_exempt
def verify(request):
    try:
        authority = request.GET.get('Authority')
        print(f"Received authority in verify: {authority}")
        status = request.GET.get('Status')

        if not authority:
            return JsonResponse({"error": "Missing authority"}, status=400)

        # بازیابی تراکنش از دیتابیس
        try:
            transaction = Transaction.objects.get(authority=authority)
        except Transaction.DoesNotExist:
            return JsonResponse({"error": "Transaction not found"}, status=404)

        # ارسال درخواست تأیید به زرین‌پال
        response = pay.verify(authority=authority, amount=transaction.amount * 10)

        if response.get("transaction"):
            if response.get("pay"):
                transaction.mark_as_paid()  # وضعیت در دیتابیس را تغییر بده
                
                # ارسال پیام موفقیت به تلگرام
                chat_id = transaction.profile.tel_id
                telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                message = f"✅ پرداخت شما با موفقیت انجام شد!\n🔹 مبلغ: {transaction.amount} تومان\n🛍 محصول: {transaction.product.name}"
                requests.post(telegram_url, json={"chat_id": chat_id, "text": message})

                return JsonResponse({"message": "Transaction successfully completed"}, status=200)

            else:
                transaction.mark_as_failed()  # اگر پرداخت قبلاً تأیید شده بود
                return JsonResponse({"message": "Transaction already verified."}, status=400)

        else:
            if response.get("status") == "ok":
                transaction.mark_as_failed()
                return JsonResponse({"error": response.get("message")}, status=400)
            elif response.get("status") == "cancel":
                transaction.mark_as_canceled()
                return JsonResponse({"error": "Transaction was canceled by user."}, status=400)

    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({"error": f"An internal error occurred. {e}"}, status=500)
