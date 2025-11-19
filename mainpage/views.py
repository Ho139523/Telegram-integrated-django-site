from django.shortcuts import render
from django.views.generic import ListView
from accounts.models import User

# Create your views here.
# class home(ListView):
    
    # template_name = 'mainpage/mainpage.html'
    
    
def home(request):
    
    context={
        "users": User.objects.filter(is_superuser=True, profilemodel__isnull=False),
    }
    
    return render(request, "mainpage/mainpage.html", context=context)