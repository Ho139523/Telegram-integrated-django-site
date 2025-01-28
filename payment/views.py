from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .zarinpal import ZarinPal
import json
from products.models import Product
from django.http import HttpResponse
import requests


pay = ZarinPal(merchant='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx', call_back_url="http://localhost:8000/verify/")


@csrf_exempt
def send_request(request):
    try:
        if request.method == "POST":
            try:
                # دریافت داده‌های JSON از body
                data = json.loads(request.body)
                print(f"Parsed Data: {data}")
                
                # استخراج product_code از data
                product_data = data.get("data", {})  # استخراج داده‌های محصول
                product_code = product_data.get("code")  # استخراج کد محصول
                print(f"Product Code: {product_code}")
                
                if not product_code:
                    return JsonResponse({"error": "Product code is required"}, status=400)

                # دریافت اطلاعات کالا
                amount = int(float(product_data.get("final_price", "0")))  # مقدار قیمت (به صورت عدد صحیح)
                description = product_data.get("description")  # توضیحات

                # ارسال درخواست به زرین‌پال
                response = pay.send_request(
                    amount=amount,
                    description=description,
                    email="admin@admin.com",  # ایمیل اختیاری
                    mobile="09123456789"  # شماره موبایل اختیاری
                )
                if response.get('error_code') is None:
                    return JsonResponse({"redirect_url": response.url})
                else:
                    return JsonResponse({"error": response.get("message")}, status=400)
            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid JSON"}, status=400)
        else:
            return JsonResponse({"error": "Invalid method"}, status=405)
            
    except Exception as e:
        # Log the error for debugging
        print(f"Error: {e}")
        return HttpResponse("An error occurred.", status=500)






def verify(request):
    response = pay.verify(request=request, amount='100000')  # مقدار `amount` واقعی باشد

    if response.get("transaction"):
        if response.get("pay"):
            return JsonResponse({"message": "تراکنش با موفقیت انجام شد"}, status=200)
        else:
            return JsonResponse({"message": "تراکنش قبلاً تایید شده است."}, status=200)
    else:
        if response.get("status") == "ok":
            return JsonResponse({"error": response.get("message")}, status=400)
        elif response.get("status") == "cancel":
            return JsonResponse({"error": "تراکنش لغو شده است."}, status=400)
