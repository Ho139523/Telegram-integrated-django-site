from django.shortcuts import render
from django.views.generic import ListView

# Create your views here.
# class home(ListView):
    
    # template_name = 'mainpage/mainpage.html'
    
    
def home(request):
    
    context={
        
    }
    
    return render(request, "mainpage/mainpage.html", context=context)