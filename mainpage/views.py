from products.models import Store
import profile
from django.shortcuts import render
from django.views.generic import ListView
from accounts.models import ProfileModel, User

# Create your views here.
# class home(ListView):
    
    # template_name = 'mainpage/mainpage.html'
    
    
from django.shortcuts import render, get_object_or_404
from products.models import Store, Product
from accounts.models import ProfileModel
from django.db.models import F
from django.core.paginator import Paginator


def home(request):
    # چک کردن ورود کاربر
    if not request.user.is_authenticated:
        server_store = Store.objects.get(name="Intelleum")
        profile = None
    else:
        print(request.user)
        profile = ProfileModel.objects.get(user=request.user)
        server_store = profile.server_store

    # گرفتن جدیدترین محصولات از دیتابیس بر اساس فروشگاه
    products = Product.objects.filter(store=server_store).order_by('-id')  # یا می‌تونید از created_at استفاده کنید
    print(products[0].main_image.url)
    # پیکربندی pagination برای جدیدترین محصولات
    paginator = Paginator(products, 8)  # نمایش 8 محصول در هر صفحه
    page_number = request.GET.get('np')  # نام پارامتر را np قرار می‌دهیم
    newest_page = paginator.get_page(page_number)

    context = {
        "profile": profile,
        "store": server_store,
        "newest_page": newest_page,  # ارسال صفحه‌بندی شده به قالب
    }

    return render(request, "mainpage/mainpage.html", context)
