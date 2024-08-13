from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages



def login_user(request):
    
    if request.method=='POST':
        username=request.POST['username']
        password=request.POST['password']
        user=authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, ('Successfully Logged in.'))
            return redirect("cv:cv")
        else:
            messages.error(request, ('User Not Found!'))
            return render(request, 'registration/login.html')
    else:
        return render(request, 'registration/login.html')
    
    
def logout_user(request):
    logout(request)
    messages.success(request, ('Successfully Logged out.'))
    return redirect("heartpred:heartpred")