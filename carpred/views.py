from django.shortcuts import render

def home(request):
    context={}
    return render(request, 'carpred/index.html', context=context)
