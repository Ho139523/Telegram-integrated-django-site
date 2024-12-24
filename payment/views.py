from django.shortcuts import render, redirect
from django.conf import settings
from zarinpal import Zarinpal

zarinpal = Zarinpal(merchant_id=settings.ZARINPAL['MERCHANT_ID'], sandbox=settings.ZARINPAL['SANDBOX'])

def payment_request(request):
    amount = 10000  # مبلغ به تومان
    description = "خرید محصول"  
    email = "user@example.com"
    mobile = "09123456789"
    
    callback_url = settings.ZARINPAL['CALLBACK_URL']
    result = zarinpal.request(amount, description, callback_url, email, mobile)
    
    if result['status'] == 100:
        return redirect(result['url'])
    else:
        return render(request, 'payment/payment_failed.html', {'error': result['status']})


def payment_verify(request):
    authority = request.GET.get('Authority')
    amount = 10000  # همان مبلغ درخواست پرداخت

    result = zarinpal.verify(amount, authority)
    
    if result['status'] == 100:
        return render(request, 'payment/payment_success.html', {'ref_id': result['ref_id']})
    else:
        return render(request, 'payment/payment_failed.html', {'error': result['status']})
