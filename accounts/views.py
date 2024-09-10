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
from django.contrib.auth.views import LoginView, PasswordChangeView, PasswordChangeDoneView, PasswordResetView, PasswordResetConfirmView
from django.urls import reverse_lazy
from .models import ProfileModel
from django.contrib.auth import get_user_model
from utils.variables.sidebaritems import sidebar
User = get_user_model()


from django.http import HttpResponse
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import generate_token
from django.core.mail import EmailMessage



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
    
    
# def signup_user(request):
    
    # if request.method=='POST':
        # form=SignUpForm(request.POST)
        # print(form.errors)
        # if form.is_valid():
            # form.save()
            # email=form.cleaned_data['email']
            # username=form.cleaned_data['username']
            # password=form.cleaned_data['password1']
            # user=authenticate(request, username=username, password=password)
            # login(request, user)
            # return redirect('accounts:login')
        # else:
            # context={'form': form}
            # return redirect('accounts:signup')    
    # else:
        # form=SignUpForm()
        # context={'form': form}
        # return render(request, 'registration/signup.html', context=context)
        
        
        
def signup_user(request):  
    if request.method == 'POST':  
        form = SignUpForm(request.POST)  
        if form.is_valid():  
            # save form in the memory not in database  
            user = form.save(commit=False)  
            user.is_active = False  
            user.save()  
            # to get the domain of the current site  
            current_site = get_current_site(request)  
            mail_subject = 'Activation link has been sent to your email id'  
            message = render_to_string('registration/acc_active_email.html', {  
                'user': user,  
                'domain': current_site.domain,  
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),  
                'token':generate_token.make_token(user),  
            })  
            to_email = form.cleaned_data.get('email')  
            email = EmailMessage(  
                        mail_subject, message, to=[to_email]  
            )  
            email.send()
            messages.add_message(request, messages.SUCCESS, "Please confirm your email address to complete the registration")
            return redirect('accounts:login') 
            
            
        else:
            
            messages.add_message(request, messages.SUCCESS, "Something went wrong!")
            return redirect('accounts:login')
            
    else:  
        form = SignUpForm()  
    return render(request, 'registration/signup.html', {'form': form})

        
        
def activate(request, uidb64, token):  
    User = get_user_model()  
    try:  
        uid = force_str(urlsafe_base64_decode(uidb64))  
        user = User.objects.get(pk=uid)  
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):  
        user = None  
    if user is not None and generate_token.check_token(user, token):  
        user.is_active = True  
        user.save()
        messages.add_message(request, messages.SUCCESS, "Your account has been activated successfully.")
        return redirect('accounts:login')
    else:
        messages.add_message(request, messages.SUCCESS, "The link is invalid or expired! Please try again.")
        return redirect('accounts:login') 
        
    
@login_required    
def profile(request, username):
    
    try:
        profile=ProfileModel.objects.get(user__username=username)
    except:
        profile={
        'user': User.objects.get(username=username),
        'fname': 'First Name',
        'lname': 'Last Name',
        'avatar': '',
        'background_pic': '',
        'birthday': '',
        'Phone': '',
        'address': '',
        }
    
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
        
        
class PasswordReset(PasswordResetView):
    
    template_name="registration/password_reset_form.html"
    success_url=reverse_lazy("accounts:login")
    
    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Recovery Email Has Been Successfully Sent To Your Email Address.")
        kwargs={
        
        }
        return reverse_lazy("accounts:login", kwargs=kwargs)
        
        
class PasswordResetConfirm(PasswordResetConfirmView):
    
    template_name="registration/password_reset_confirm.html"
    success_url=reverse_lazy("accounts:login")
    
    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Your Password Has Been Successfully Changed.")
        kwargs={
        
        }
        return reverse_lazy("accounts:login", kwargs=kwargs)
    
        
        
def billing(request, username):
    try:
        profile=ProfileModel.objects.get(user__username=username)
    except:
        messages.add_message(request, messages.WARNING, "Please complete your profile first!")
        return redirect('accounts:profile', username=username)
    context={
        "profile": profile,
        "sidebar": [(item, logo ) for item , logo in sidebar],
        "view": "Billing",
        "app_name": "accounts:"
    }
    
    return render(request, 'registration/dashboard/billing.html', context=context)