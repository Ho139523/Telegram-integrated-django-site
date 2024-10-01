from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import User
from .form import SignUpForm, HeaderImageForm, AvatarImageForm, ProfileUpdateForm, ShippingAddressForm, ShippingAddressFormSet
from django.contrib.auth.views import LoginView, PasswordChangeView, PasswordChangeDoneView, PasswordResetView, PasswordResetConfirmView
from django.urls import reverse_lazy, reverse
from .models import ProfileModel, ShippingAddressModel
from django.forms import inlineformset_factory
from django.contrib.auth import get_user_model
User = get_user_model()


from django.http import HttpResponse
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import generate_token
from django.core.mail import EmailMessage



        
class login(LoginView):
    
    def get_success_url(self):
        
        username=self.request.POST['username']
        return reverse_lazy("accounts:profile", kwargs={"username":username})
        
        
 
    
    
def logout_user(request):
    logout(request)
    return redirect("heartpred:heartpred")
    
 
        
        
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
            
            messages.add_message(request, messages.WARNING, "Something went wrong!")
            return redirect('accounts:signup')
            
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
        
        profile=ProfileModel(user=user)
        shippingaddress=ShippingAddressModel(profile=profile)
        user.profilemodel.save()
        profile.save()
        shippingaddress.save()
        messages.add_message(request, messages.SUCCESS, "Your account has been activated successfully.")
        return redirect('accounts:login')
    else:
        messages.add_message(request, messages.SUCCESS, "The link is invalid or expired! Please try again.")
        return redirect('accounts:login') 
        

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


@login_required
def profile(request, username):
   
    profile=ProfileModel.objects.get(user__username=username)
    shippingaddress=ShippingAddressModel.objects.get(profile=profile)
    header_form = HeaderImageForm()
    avatar_form = AvatarImageForm()
    update_form = ProfileUpdateForm(initial={
                                            "fname": profile.fname,
                                            "lname": profile.lname,
                                            "Phone": profile.Phone,
                                            "address": profile.address,
                                            "about_me": profile.about_me,
                                            "birthday": profile.birthday,
                                            "tweeter": profile.tweeter,
                                            "instagram": profile.instagram,
                                            },)
    address_formset=ShippingAddressFormSet(initial=[{
                                                    "shipping_line1": shippingaddress.shipping_line1,
                                                    "shipping_line2": shippingaddress.shipping_line2,
                                                    "shipping_city": shippingaddress.shipping_city,
                                                    "shipping_province": shippingaddress.shipping_province,
                                                    "shipping_zip": shippingaddress.shipping_zip,
                                                    "shipping_home_phone": shippingaddress.shipping_home_phone,
                                                    },])
    
    
    context={
        "profile": profile,
        'view': 'Profile',
        "header_form": header_form,
        "avatar_form": avatar_form,
        "update_form": update_form,
        "address_formset": address_formset,

    }
    return render(request, "registration/dashboard/profile.html", context=context)
    

class ChangePassword(LoginRequiredMixin, PasswordChangeView):
    
    template_name="registration/dashboard/password_change.html"
    
    def get_success_url(self):
        kwargs = {
            "username": self.kwargs.get("username")
        }
        return reverse_lazy("accounts:profile", kwargs=kwargs)

    def get_form(self, form_class=None):
        """Override get_form to remove old password field for users without a password"""
        form = super().get_form(form_class)
        user = self.get_user()
        if not user.has_usable_password():
            form.fields.pop('old_password')
        return form

    def get_user(self):
        """Get the user from the URL or the request."""
        username = self.kwargs.get("username")
        return User.objects.get(username=username)

    def form_valid(self, form):
        """If the form is valid, proceed to change the password."""
        messages.add_message(self.request, messages.SUCCESS, "Your password has been successfully changed.")
        return super().form_valid(form)

    def form_invalid(self, form):
        """If the form is invalid, handle errors and display messages."""
        for error in form.errors.values():
            messages.add_message(self.request, messages.ERROR, error)
        
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        """Pass additional context data to the template."""
        context = super().get_context_data(**kwargs)
        username = self.kwargs.get("username")
        user = self.get_user()
        context["username"] = username
        context["has_password"] = user.has_usable_password()
        context["view"] = "Change Password"
        return context
        
        
    
@login_required        
def billing(request, username):
    try:
        profile=ProfileModel.objects.get(user__username=username)
    except:
        messages.add_message(request, messages.WARNING, "Please complete your profile first!")
        return redirect('accounts:profile', username=username)
    context={
        "profile": profile,
        "view": "Billing",
    }
    
    return render(request, 'registration/dashboard/billing.html', context=context)
    


@login_required
def change_header_image(request):
    if request.method == 'POST':
        form = HeaderImageForm(request.POST, request.FILES, instance=request.user.profilemodel)
        if form.is_valid():
            form.save()
            return redirect('accounts:profile', username=request.user.username)  # Redirect to the profile page after saving
    else:
        form = HeaderImageForm(instance=request.user.profilemodel)
    
    return render(request, 'registration/dashboard/profile.html', {'header_form': form})
    
    
    
@login_required
def change_avatar_image(request):
    if request.method == 'POST':
        form = AvatarImageForm(request.POST, request.FILES, instance=request.user.profilemodel)
        if form.is_valid():
            form.save()
            return redirect('accounts:profile', username=request.user.username)  # Redirect to the profile page after saving
    else:
        form = AvatarImageForm(instance=request.user.profilemodel)
    
    return render(request, 'registration/dashboard/profile.html', {'avatar_form': form})
    
    

@login_required
def profile_update_view(request):
    profile = request.user.profilemodel  # Get the profile associated with the user
    shipping_address = getattr(profile, 'shippingaddressmodel', None)  # Handle if no address exists

    # Forms for updating avatar and header images (if needed)
    header_form = HeaderImageForm()
    avatar_form = AvatarImageForm()

    # Initialize the profile update form and shipping address form
    update_form = ProfileUpdateForm(instance=profile)
    address_form = ShippingAddressForm(instance=shipping_address)

    if request.method == 'POST':
        # Handle the profile form submission
        update_form = ProfileUpdateForm(request.POST, instance=profile)
        address_form = ShippingAddressForm(request.POST, instance=shipping_address)

        if update_form.is_valid() and address_form.is_valid():
            # Save profile changes
            profile = update_form.save()

            # Save or create the new shipping address
            shipping_address = address_form.save(commit=False)
            shipping_address.profile = profile  # Ensure the address is linked to the profile
            shipping_address.save()

            # Redirect after successful save
            return render(request, 'registration/dashboard/profile.html', {
                'update_form': update_form,
                'address_form': address_form,
                'profile': profile,
                'view': 'Profile',
                'header_form': header_form,
                'avatar_form': avatar_form,
            })
        else:
            # Debug form errors
            print(update_form.errors)
            print(address_form.errors)

    # If it's a GET request, redirect to the profile page
    return redirect('accounts:profile', username=request.user.username)



