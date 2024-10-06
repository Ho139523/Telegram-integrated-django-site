from django.shortcuts import render
from django.views.generic import ListView
from products.models import TutorialModel
from accounts.models import User

# Create your views here.
# class home(ListView):
    
    # template_name = 'mainpage/mainpage.html'
    
    
def home(request):
    
    context={
        "tutorials": TutorialModel.objects.filter(status=True),
        "users": User.objects.filter(is_superuser=True)
    }
    
    return render(request, "mainpage/mainpage.html", context=context)