from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import User
from .form import SignUpForm, HeaderImageForm, AvatarImageForm, ProfileUpdateForm, ShippingAddressForm
from django.contrib.auth.views import LoginView, PasswordChangeView, PasswordChangeDoneView, PasswordResetView, PasswordResetConfirmView
from django.urls import reverse_lazy, reverse
from .models import ProfileModel, Address
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


#countries, provinces and cities
from django.http import JsonResponse
import pycountry


        
class login(LoginView):
    
    def get_success_url(self):
        
        username=self.request.POST['username'].strip().lower()
        return reverse_lazy("accounts:profile", kwargs={"username":username})
        
        
 
    
    
def logout_user(request):
    logout(request)
    return redirect("mainpage:home")
    
 
        
        
def signup_user(request):  
    if request.method == 'POST':  
        form = SignUpForm(request.POST)  
        if form.is_valid():  
            user = form.save(commit=False)  
            user.is_active = False  
            user.save()
            
            # Create ProfileModel immediately after user creation
            ProfileModel.objects.create(user=user)
            
            current_site = get_current_site(request)  
            mail_subject = 'Activation link has been sent to your email id'  
            message = render_to_string('registration/acc_active_email.html', {  
                'user': user,  
                'domain': current_site.domain,  
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),  
                'token': generate_token.make_token(user),  
            })  
            to_email = form.cleaned_data.get('email')  
            email = EmailMessage(mail_subject, message, to=[to_email])  
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
        try:
          user.is_active = True  
          user.save()
        
          # Use get_or_create to avoid duplicate profiles
          profile, created = ProfileModel.objects.get_or_create(user=user)

          # Create and save a shipping address if it doesn't already exist
          if not hasattr(profile, 'shippingaddressmodel'):
              shippingaddress = ShippingAddressModel(profile=profile)
              shippingaddress.save()
        
          user.profilemodel.save()
          profile.save()
          messages.add_message(request, messages.SUCCESS, "Your account has been activated successfully.")
          return redirect('accounts:login')
        except Exception as e:
          print(f"\n\n the error is: {e}\n\n")
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
    address=Address.objects.get(profile=profile, shipping_is_active=True)
    header_form = HeaderImageForm()
    avatar_form = AvatarImageForm()
    update_form = ProfileUpdateForm(initial={
        "fname": profile.fname,
        "lname": profile.lname,
        "Phone": profile.Phone,
        "about_me": profile.about_me,
        "birthday": profile.birthday,
        "tweeter": profile.tweeter,
        "instagram": profile.instagram,
    })
                                            
    updated_address = ShippingAddressForm(initial={
        "shipping_line1": address.shipping_line1,
        "shipping_line2": address.shipping_line2,
        "shipping_city": address.shipping_city,
        "shipping_country": address.shipping_country,
        "shipping_province": address.shipping_province,
        "shipping_zip": address.shipping_zip_code,
        "shipping_home_phone": address.shipping_home_phone,
    })
    
    
    context={
        "profile": profile,
        'view': 'Profile',
        "header_form": header_form,
        "avatar_form": avatar_form,
        "update_form": update_form,
        "updated_address": updated_address,

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
        context['user']=user
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
            return redirect('accounts:profile', username=request.user.username)
        else:
            # Debug form errors
            print(update_form.errors)
            print(address_form.errors)

    context = {
        'update_form': update_form,
        'address_form': address_form,
        'profile': profile,
        'view': 'Profile',
        'header_form': header_form,
        'avatar_form': avatar_form,
    }

    return render(request, 'registration/dashboard/profile.html', context)




from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json




import os
from pathlib import Path 


BASE_DIR = Path(__file__).resolve().parent.parent 
JSON_DATA_PATH = os.path.join(BASE_DIR, "utils/Data/countries_full_multilang.json")





def load_geodata():
    with open(JSON_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@csrf_exempt
@require_POST
def get_provinces(request):
    try:
        data = json.loads(request.body)
        country_code = data.get("country")
    except Exception:
        return JsonResponse({"error": "Invalid request body"}, status=400)

    if not country_code:
        return JsonResponse({"error": "Country code is missing"}, status=400)

    lang = getattr(request.user, "lang", "en")

    geodata = load_geodata()
    country_info = geodata.get(country_code)

    if not country_info:
        return JsonResponse({"error": "Country not found"}, status=404)

    provinces = []
    for code, province_data in country_info.get("provinces", {}).items():
        name = province_data.get("names", {}).get(lang) or province_data.get("names", {}).get("en") or code
        provinces.append({"code": code, "name": name})

    return JsonResponse({"provinces": provinces})


@csrf_exempt
@require_POST
def get_cities(request):
    try:
        data = json.loads(request.body)
        country_code = data.get("country")
        province_code = data.get("province")
    except Exception:
        return JsonResponse({"error": "Invalid request body"}, status=400)

    if not country_code or not province_code:
        return JsonResponse({"error": "Country and Province codes are required"}, status=400)

    lang = getattr(request.user, "lang", "en")

    geodata = load_geodata()
    country_info = geodata.get(country_code)

    if not country_info:
        return JsonResponse({"error": "Country not found"}, status=404)

    province_info = country_info.get("provinces", {}).get(province_code)
    if not province_info:
        return JsonResponse({"error": "Province not found"}, status=404)

    cities = []
    for code, city_data in province_info.get("cities", {}).items():
        name = city_data.get("names", {}).get(lang) or city_data.get("names", {}).get("en") or code
        cities.append({"code": code, "name": name})

    return JsonResponse({"cities": cities})

