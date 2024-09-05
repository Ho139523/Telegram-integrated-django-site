from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib import messages
from .models import User
from .form import SignUpForm
from django.contrib.auth.views import LoginView, PasswordChangeView, PasswordChangeDoneView
from django.urls import reverse_lazy
from .models import ProfileModel
from django.contrib.auth import get_user_model
from utils.variables.sidebaritems import sidebar
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
        return reverse_lazy("accounts:profile", kwargs={"username":username})
        
        
 
    
    
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
            # login(request, user)
            return redirect('accounts:login')
        else:
            context={'form': form}
            return redirect('accounts:signup')    
    else:
        form=SignUpForm()
        context={'form': form}
        return render(request, 'registration/signup.html', context=context)
        
    
@login_required    
def profile(request, username):
    
    profile=ProfileModel.objects.get(user__username=username)
    
    context={
        "profile": profile,
        "sidebar": [(item, logo ) for item , logo in sidebar],
        "view": "Profile",
        "app_name": "accounts:"
    }
    return render(request, "registration/dashboard/profile.html", context=context)
    
    
class ChangePassword(LoginRequiredMixin, PasswordChangeView):
    
    template_name="registration/dashboard/password_change.html"
    
    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Your password has been successfully changed.")
        kwargs={
        "username": self.kwargs.get("username")
        }
        return reverse_lazy("accounts:profile", kwargs=kwargs)
    
    def get_context_data(self, **kwargs):
        data=super().get_context_data(**kwargs)
        username=self.kwargs.get("username")
        data["profile"]=ProfileModel.objects.get(user__username=username)
        data["sidebar"]=[(item, logo ) for item , logo in sidebar]
        data["view"]="Change Password"
        data["app_name"]="accounts:"
        form=PasswordChangeForm(self.request.POST)
        
        return data
        
        
        
        
# class PasswordChangeDone(LoginRequiredMixin, PasswordChangeDoneView):
    # template_name = "registration/dashboard/profile.html"
    
    
    # def dispatch(self, *args, **kwargs):

        # messages.add_message(self.request, messages.SUCCESS, "Your password has been successfully changed.")
        # return super().dispatch(*args, **kwargs)
        
    