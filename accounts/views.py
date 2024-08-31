from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from .form import SignUpForm
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
User = get_user_model()



def login_user(request):
    
    if request.method=='POST':
        username=request.POST['username']
        password=request.POST['password']
        user=authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("cv:cv", username=username)
        else:
            return render(request, 'registration/login1.html')
    else:
        return render(request, 'registration/login1.html')
        
        
class login(LoginView):
    
    def get_success_url(self):
        
        username=self.request.POST['username']
        print(username)
        return reverse_lazy("cv:cv", kwargs={"username":username})
        
        
 
    
    
def logout_user(request):
    logout(request)
    return redirect("heartpred:heartpred")
    
    
def signup_user(request):
    
    if request.method=='POST':
        form=SignUpForm(request.POST)
        print(form.errors)
        if form.is_valid():
            form.save()
            email=form.cleaned_data['email']
            username=form.cleaned_data['username']
            password=form.cleaned_data['password1']
            user=authenticate(request, username=username, password=password)
            login(request, user)
            return redirect('cv:cv', username=username)
        else:
            context={'form': form}
            return redirect('accounts:signup')    
    else:
        form=SignUpForm()
        context={'form': form}
        return render(request, 'registration/signup1.html', context=context)
            
