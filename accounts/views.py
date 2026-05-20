# accounts/views.py
from django.shortcuts import render, redirect, get_object_or_404
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
from AI.settings import current_site as settings_current_site


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
from django.db.models import Q


        
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
            
            mail_subject = 'Activation link has been sent to your email id'  
            message = render_to_string('registration/acc_active_email.html', {  
                'user': user,  
                'domain': settings_current_site,  
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
              shippingaddress = Address(profile=profile)
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
    user = get_object_or_404(User, username=username)
    profile = user.profilemodel
    address = profile.get_active_address()

    context = {
        'user': user,
        'profile': profile,
        'view': 'Profile',  # <-- Add this
        'sidebar': [("profile", "person"), ("settings", "settings")],  # example
        'app_name': 'accounts:',
    }

    if address:
        context.update({
            "shipping_line1": address.shipping_line1,
            "shipping_line2": address.shipping_line2,
            "city": address.shipping_city,
            "province": address.shipping_province,
            "country": address.shipping_country,
            "postal_code": address.shipping_zip_code,
        })
    else:
        # Default empty values if no address exists yet
        context.update({
            "shipping_line1": "",
            "shipping_line2": "",
            "city": "",
            "province": "",
            "country": "",
            "postal_code": "",
        })

    return render(request, "registration/dashboard/profile.html", context)



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




from rest_framework import viewsets, permissions
from .models import User, ProfileModel, Address
from .serializers import UserSerializer, ProfileSerializer, AddressSerializer
from rest_framework import generics
from .serializers import RegisterSerializer
from rest_framework.permissions import IsAuthenticated
from utils.permissions import IsOwnerOrReadOnly, IsAdminOrReadOnly

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class ProfileViewSet(viewsets.ModelViewSet):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return ProfileModel.objects.all()
        return ProfileModel.objects.filter(user=user)

    def perform_update(self, serializer):
        # اطمینان از اینکه کاربر فقط پروفایل خودش را تغییر میدهد
        serializer.save()


class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


from rest_framework import generics
from .serializers import RegisterSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]



from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import ProfileSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    profile = getattr(request.user, 'profilemodel', None)
    return Response({
        "user": request.user.username,
        "email": request.user.email,
        "profile": ProfileSerializer(profile).data if profile else None
    })






#########################


# accounts/views.py
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import ProfileModel
from .serializers import BotProfileSerializer, BotProfileCheckSerializer
from utils.permissions import BotSignaturePermission, IsAdminOrReadOnly
from utils.balebot.nested_crud_mixin import NestedCRUDMixin  # اضافه کردن mixin جدید


class BotProfileViewSet(
    NestedCRUDMixin,  # ✅ اضافه شد - این خط تمام قابلیت‌های nested CRUD را اضافه می‌کند
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """
    Complete CRUD operations for Profile model with automatic nested relations support
    Works with both tel_id and bale_id as identifiers
    Accessible only with HMAC signature authentication
    
    ========== PROFILE CRUD ENDPOINTS ==========
    - POST   /api/bot/profiles/              - Create or update (upsert) profile
    - GET    /api/bot/profiles/<id>/         - Get profile by identifier
    - PUT    /api/bot/profiles/<id>/         - Full update
    - PATCH  /api/bot/profiles/<id>/         - Partial update
    - DELETE /api/bot/profiles/<id>/         - Delete profile
    
    ========== UTILITY ENDPOINTS ==========
    - POST   /api/bot/profiles/check/        - Check if profile exists
    - POST   /api/bot/profiles/merge/        - Merge two profiles (Telegram + Bale)
    
    ========== NESTED RELATIONS ENDPOINTS (Auto-generated) ==========
    - GET    /api/bot/profiles/<id>/relations/     - List all accessible relations
    - GET    /api/bot/profiles/<id>/<relation>/    - Get relation data
    - POST   /api/bot/profiles/<id>/<relation>/    - Create/update relation
    - PUT    /api/bot/profiles/<id>/<relation>/    - Full update relation
    - PATCH  /api/bot/profiles/<id>/<relation>/    - Partial update relation
    - DELETE /api/bot/profiles/<id>/<relation>/    - Delete/disconnect relation
    - POST   /api/bot/profiles/<id>/batch/         - Batch update multiple relations
    
    Examples of relations (auto-discovered):
    - owned_store     (OneToOne with Store)
    - server_store    (ForeignKey to Store)
    - addresses       (ForeignKey to Address)
    - transactions    (ForeignKey to Transaction)
    - carts           (ForeignKey to Cart)
    - user            (OneToOne with User)
    """
    
    # تنظیمات NestedCRUDMixin
    EXCLUDED_RELATIONS = [
        'hidden_videos',      # JSONField است نه رابطه واقعی
        # 'user',             // اگر نمی‌خواهید user از طریق API expose شود
    ]
    NESTED_DEPTH = 1  # عمق nested serialization (0=فقط IDها، 1=داده‌های سطح اول)
    
    queryset = ProfileModel.objects.all()
    serializer_class = BotProfileSerializer
    permission_classes = []
    lookup_field = 'identifier'
    lookup_value_regex = '[^/.]+'
    throttle_classes = []

    def get_object_by_identifier(self, identifier: str) -> ProfileModel:
        """
        Get profile by either tel_id or bale_id
        """
        try:
            profile = ProfileModel.objects.get(
                Q(tel_id=identifier) | Q(bale_id=identifier)
            )
            return profile
        except ProfileModel.DoesNotExist:
            raise ProfileModel.DoesNotExist(f"Profile with identifier '{identifier}' not found")

    # ============================================================
    # CHECK ENDPOINT (Optional - for backward compatibility)
    # ============================================================
    @action(detail=False, methods=['post'], url_path='check', serializer_class=BotProfileCheckSerializer)
    def check_exists(self, request):
        """
        Check if profile exists by tel_id or bale_id
        This is optional - the main create endpoint already does upsert.
        Use this if you need to check existence without creating/updating.
        
        Request body:
            {"identifier": "123456789"} 
            OR {"tel_id": "...", "bale_id": "..."}
        """
        serializer = BotProfileCheckSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        identifier = serializer.validated_data.get('identifier')
        tel_id = serializer.validated_data.get('tel_id')
        bale_id = serializer.validated_data.get('bale_id')
        
        if identifier:
            exists = ProfileModel.objects.filter(
                Q(tel_id=identifier) | Q(bale_id=identifier)
            ).exists()
            
            profile = None
            if exists:
                profile = ProfileModel.objects.filter(
                    Q(tel_id=identifier) | Q(bale_id=identifier)
                ).first()
            
            return Response({
                "success": True,
                "exists": exists,
                "identifier": identifier,
                "profile_id": profile.id if profile else None,
            }, status=status.HTTP_200_OK)
        
        elif tel_id or bale_id:
            query = Q()
            if tel_id:
                query |= Q(tel_id=tel_id)
            if bale_id:
                query |= Q(bale_id=bale_id)
            exists = ProfileModel.objects.filter(query).exists()
            
            profile = None
            if exists:
                profile = ProfileModel.objects.filter(query).first()
            
            return Response({
                "success": True,
                "exists": exists,
                "tel_id": tel_id,
                "bale_id": bale_id,
                "profile_id": profile.id if profile else None,
            }, status=status.HTTP_200_OK)
        
        return Response({
            "success": False,
            "error": "No identifier provided"
        }, status=status.HTTP_400_BAD_REQUEST)

    # ============================================================
    # MAIN CREATE/UPSERT ENDPOINT (Recommended - use this!)
    # ============================================================
    def create(self, request, *args, **kwargs):
        """
        Create or update profile (UPSERT) with tel_id or bale_id.
        This endpoint automatically handles both create and update in ONE request.
        
        Request body examples:
            1. Telegram user:  {"tel_id": "123456789", "fname": "John", "lname": "Doe", "telegram": "@john"}
            2. Bale user:      {"bale_id": "987654321", "fname": "Ali", "lname": "Rezaei", "bale": "@ali"}
            3. Both platforms: {"tel_id": "123456789", "bale_id": "987654321", "fname": "John", ...}
        
        Response:
            - If profile existed: status 200, {"success": True, "created": False, "updated": True, "data": {...}}
            - If profile created: status 201, {"success": True, "created": True, "updated": False, "data": {...}}
        """
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                "success": False,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        tel_id = serializer.validated_data.get('tel_id')
        bale_id = serializer.validated_data.get('bale_id')
        
        # Validate: at least one identifier must be provided
        if not tel_id and not bale_id:
            return Response({
                "success": False,
                "error": "Either tel_id or bale_id must be provided"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Build query to find existing profile
        query = Q()
        if tel_id:
            query |= Q(tel_id=tel_id)
        if bale_id:
            query |= Q(bale_id=bale_id)
        
        existing_profile = ProfileModel.objects.filter(query).first()
        
        if existing_profile:
            # UPDATE existing profile
            update_data = {}
            
            # Add all fields from request (excluding identifiers that are None)
            for key, value in serializer.validated_data.items():
                if value is not None:
                    update_data[key] = value
            
            # Special handling: don't remove existing identifiers if not provided
            if tel_id is None and existing_profile.tel_id:
                update_data.pop('tel_id', None)
            if bale_id is None and existing_profile.bale_id:
                update_data.pop('bale_id', None)
            
            # Update the profile
            for key, value in update_data.items():
                setattr(existing_profile, key, value)
            existing_profile.save()
            
            # Return updated profile
            output_serializer = self.get_serializer(existing_profile)
            return Response({
                "success": True,
                "created": False,
                "updated": True,
                "data": output_serializer.data
            }, status=status.HTTP_200_OK)
        
        else:
            # CREATE new profile
            profile = serializer.save()
            output_serializer = self.get_serializer(profile)
            return Response({
                "success": True,
                "created": True,
                "updated": False,
                "data": output_serializer.data
            }, status=status.HTTP_201_CREATED)

    # ============================================================
    # RETRIEVE (GET by identifier)
    # ============================================================
    def retrieve(self, request, identifier=None, *args, **kwargs):
        """
        Get profile by either tel_id or bale_id
        
        Optional query params:
        - include_relations: comma-separated list of relations to include
        - depth: nesting depth for relations (0-2)
        
        Example: /api/bot/profiles/123/?include_relations=owned_store,server_store&depth=1
        """
        try:
            profile = self.get_object_by_identifier(identifier)
            
            # Check if we need to include relations
            include_relations = request.query_params.get('include_relations', '').split(',')
            include_relations = [r.strip() for r in include_relations if r.strip()]
            
            if include_relations and include_relations[0]:
                # Use select_related for performance
                select_related_fields = []
                for relation in include_relations:
                    if relation in ['owned_store', 'server_store', 'user']:
                        select_related_fields.append(relation)
                
                if select_related_fields:
                    profile = ProfileModel.objects.select_related(*select_related_fields).get(id=profile.id)
            
            serializer = self.get_serializer(profile)
            data = serializer.data
            
            # Add nested relations if requested
            if include_relations and include_relations[0]:
                for relation_name in include_relations:
                    if hasattr(profile, relation_name) and self._is_valid_relation(relation_name):
                        related = getattr(profile, relation_name)
                        if related:
                            from utils.dynamic_serializers import get_serializer_for_model
                            if hasattr(related, 'all'):  # ManyToMany or reverse
                                ser = get_serializer_for_model(related.model)
                                data[relation_name] = ser(related.all(), many=True).data
                            else:  # OneToOne or ForeignKey
                                ser = get_serializer_for_model(related.__class__)
                                data[relation_name] = ser(related).data
            
            return Response({
                "success": True,
                "data": data
            }, status=status.HTTP_200_OK)
            
        except ProfileModel.DoesNotExist as e:
            return Response({
                "success": False,
                "error": str(e),
                "identifier": identifier
            }, status=status.HTTP_404_NOT_FOUND)

    # ============================================================
    # UPDATE (Full update by identifier)
    # ============================================================
    def update(self, request, identifier=None, *args, **kwargs):
        """Full update profile by tel_id or bale_id"""
        try:
            profile = self.get_object_by_identifier(identifier)
        except ProfileModel.DoesNotExist as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(profile, data=request.data)
        
        if not serializer.is_valid():
            return Response({
                "success": False,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    # ============================================================
    # PARTIAL UPDATE (PATCH by identifier)
    # ============================================================
    def partial_update(self, request, identifier=None, *args, **kwargs):
        """Partial update profile by tel_id or bale_id"""
        try:
            profile = self.get_object_by_identifier(identifier)
        except ProfileModel.DoesNotExist as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        
        if not serializer.is_valid():
            return Response({
                "success": False,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    # ============================================================
    # DELETE (by identifier)
    # ============================================================
    def destroy(self, request, identifier=None, *args, **kwargs):
        """Delete profile by tel_id or bale_id"""
        try:
            profile = self.get_object_by_identifier(identifier)
            
            # Optional: cascade delete related objects
            cascade = request.query_params.get('cascade', 'false').lower() == 'true'
            
            if cascade:
                # Delete related objects first
                if hasattr(profile, 'owned_store') and profile.owned_store:
                    profile.owned_store.delete()
                profile.addresses.all().delete()
                # Note: transactions and carts might need different handling
            
            profile.delete()
            
            return Response({
                "success": True,
                "message": "Profile deleted successfully"
            }, status=status.HTTP_200_OK)
            
        except ProfileModel.DoesNotExist as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_404_NOT_FOUND)

    # ============================================================
    # MERGE PROFILES (Telegram + Bale)
    # ============================================================
    @action(detail=False, methods=['post'], url_path='merge')
    def merge_profiles(self, request):
        """
        Merge two profiles (Telegram + Bale) into one unified profile
        
        Request body:
            {
                "main_identifier": "123456789",      # tel_id or bale_id of main profile
                "secondary_identifier": "987654321",  # tel_id or bale_id to merge into main
                "merge_relations": true               # optionally merge related objects
            }
        """
        main_id = request.data.get('main_identifier')
        secondary_id = request.data.get('secondary_identifier')
        merge_relations = request.data.get('merge_relations', False)
        
        if not main_id or not secondary_id:
            return Response({
                "success": False,
                "error": "Both main_identifier and secondary_identifier are required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            main_profile = self.get_object_by_identifier(main_id)
            secondary_profile = self.get_object_by_identifier(secondary_id)
            
            # Prevent self-merge
            if main_profile.id == secondary_profile.id:
                return Response({
                    "success": False,
                    "error": "Cannot merge profile with itself"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Transfer data from secondary to main (only if main doesn't have them)
            fields_to_transfer = [
                'fname', 'lname', 'phone', 'telegram', 'bale',
                'avatar', 'birthday', 'about_me', 'instagram', 'tweeter'
            ]
            
            for field in fields_to_transfer:
                if not getattr(main_profile, field) and getattr(secondary_profile, field):
                    setattr(main_profile, field, getattr(secondary_profile, field))
            
            # Ensure both identifiers are present in main profile
            if secondary_profile.tel_id and not main_profile.tel_id:
                main_profile.tel_id = secondary_profile.tel_id
            if secondary_profile.bale_id and not main_profile.bale_id:
                main_profile.bale_id = secondary_profile.bale_id
            
            # Merge related objects if requested
            if merge_relations:
                # Merge addresses
                for address in secondary_profile.addresses.all():
                    address.profile = main_profile
                    address.save()
                
                # Merge carts
                for cart in secondary_profile.carts.all():
                    cart.profile = main_profile
                    cart.save()
                
                # Merge transactions
                for transaction in secondary_profile.transactions.all():
                    transaction.profile = main_profile
                    transaction.save()
            
            main_profile.save()
            
            # Soft delete secondary profile
            # Note: Add is_active and merged_into fields to ProfileModel if needed
            # secondary_profile.is_active = False
            # secondary_profile.merged_into = main_profile
            # secondary_profile.save()
            
            # For now, just delete or keep as is
            # secondary_profile.delete()  # Uncomment if you want to delete
            
            return Response({
                "success": True,
                "message": "Profiles merged successfully",
                "data": self.get_serializer(main_profile).data
            }, status=status.HTTP_200_OK)
            
        except ProfileModel.DoesNotExist as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_404_NOT_FOUND)
        

    
    def get_object_by_identifier(self, identifier: str) -> ProfileModel:
        """
        Get profile by either tel_id or bale_id
        """
        try:
            profile = ProfileModel.objects.get(
                Q(tel_id=identifier) | Q(bale_id=identifier)
            )
            return profile
        except ProfileModel.DoesNotExist:
            raise ProfileModel.DoesNotExist(f"Profile with identifier '{identifier}' not found")
    
    # ============================================================
    # OVERRIDE NestedCRUDMixin METHODS FOR PROPER LOOKUP
    # ============================================================
    
    def get_relation_instance(self, identifier):
        """Helper method to get instance by identifier"""
        if hasattr(self, 'get_object_by_identifier'):
            return self.get_object_by_identifier(identifier)
        return self.get_queryset().get(pk=identifier)
    
    @action(detail=False, methods=['get'], url_path='(?P<identifier>[^/.]+)/relations')
    def list_relations(self, request, identifier=None):
        """لیست تمام روابط قابل دسترس"""
        try:
            instance = self.get_relation_instance(identifier)
            
            relations = {}
            for field in instance._meta.get_fields():
                if self._is_valid_relation(field.name):
                    relations[field.name] = {
                        'type': field.__class__.__name__,
                        'model': field.related_model.__name__ if field.related_model else None,
                        'url': f"/api/bot/profiles/{identifier}/{field.name}/"
                    }
            
            return Response({
                "success": True,
                "profile_id": instance.id,
                "identifier": identifier,
                "relations": relations
            })
        except ProfileModel.DoesNotExist as e:
            return Response({"error": str(e)}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=400)
    
    @action(detail=False, methods=['get'], url_path='(?P<identifier>[^/.]+)/(?P<relation_name>[a-zA-Z_]+)')
    def get_relation(self, request, identifier=None, relation_name=None):
        """دریافت داده‌های یک رابطه خاص"""
        try:
            instance = self.get_relation_instance(identifier)
            
            if not self._is_valid_relation(relation_name):
                return Response({
                    "success": False,
                    "error": f"Relation '{relation_name}' is not accessible"
                }, status=400)
            
            related = self._get_related_object(instance, relation_name)
            
            if related is None:
                return Response({
                    "success": False,
                    "error": f"No {relation_name} found for profile {identifier}"
                }, status=404)
            
            # تشخیص نوع و سریالایز کردن
            if hasattr(related, 'all'):  # ManyToMany یا reverse relation
                if related.count() == 0:
                    return Response({
                        "success": True,
                        "relation": relation_name,
                        "data": []
                    })
                serializer_class = get_serializer_for_model(related.model)
                serializer = serializer_class(related.all(), many=True)
            else:  # OneToOne یا ForeignKey
                serializer_class = get_serializer_for_model(related.__class__)
                serializer = serializer_class(related)
            
            return Response({
                "success": True,
                "relation": relation_name,
                "profile_id": instance.id,
                "data": serializer.data
            })
            
        except ProfileModel.DoesNotExist as e:
            return Response({"error": str(e)}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=400)
    
    @action(detail=False, methods=['post', 'put', 'patch'], 
            url_path='(?P<identifier>[^/.]+)/(?P<relation_name>[a-zA-Z_]+)')
    def update_relation(self, request, identifier=None, relation_name=None):
        """ایجاد یا بروزرسانی یک رابطه"""
        try:
            instance = self.get_relation_instance(identifier)
            
            if not self._is_valid_relation(relation_name):
                return Response({"error": "Invalid relation"}, status=400)
            
            success = self._set_related_object(instance, relation_name, request.data)
            
            if success:
                instance.save()
                
                # برگرداندن داده به‌روز شده
                related = self._get_related_object(instance, relation_name)
                if hasattr(related, 'all'):
                    if related.count() == 0:
                        data = []
                    else:
                        serializer_class = get_serializer_for_model(related.model)
                        serializer = serializer_class(related.all(), many=True)
                        data = serializer.data
                else:
                    serializer_class = get_serializer_for_model(related.__class__)
                    serializer = serializer_class(related)
                    data = serializer.data
                
                return Response({
                    "success": True,
                    "action": "updated",
                    "relation": relation_name,
                    "profile_id": instance.id,
                    "data": data
                })
            else:
                return Response({"error": "Failed to update relation"}, status=400)
                
        except ProfileModel.DoesNotExist as e:
            return Response({"error": str(e)}, status=404)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=400)
    
    # ============================================================
    # MAIN CRUD METHODS (با پشتیبانی از identifier)
    # ============================================================
    
    def retrieve(self, request, identifier=None, *args, **kwargs):
        """Get profile by either tel_id or bale_id"""
        try:
            profile = self.get_object_by_identifier(identifier)
            serializer = self.get_serializer(profile)
            return Response({
                "success": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except ProfileModel.DoesNotExist as e:
            return Response({
                "success": False,
                "error": str(e),
                "identifier": identifier
            }, status=status.HTTP_404_NOT_FOUND)
    
    def create(self, request, *args, **kwargs):
        """Create or update profile (UPSERT)"""
        # ... کد create شما به همان صورت باقی می‌ماند ...
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                "success": False,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        tel_id = serializer.validated_data.get('tel_id')
        bale_id = serializer.validated_data.get('bale_id')
        
        if not tel_id and not bale_id:
            return Response({
                "success": False,
                "error": "Either tel_id or bale_id must be provided"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        query = Q()
        if tel_id:
            query |= Q(tel_id=tel_id)
        if bale_id:
            query |= Q(bale_id=bale_id)
        
        existing_profile = ProfileModel.objects.filter(query).first()
        
        if existing_profile:
            update_data = {}
            for key, value in serializer.validated_data.items():
                if value is not None:
                    update_data[key] = value
            
            if tel_id is None and existing_profile.tel_id:
                update_data.pop('tel_id', None)
            if bale_id is None and existing_profile.bale_id:
                update_data.pop('bale_id', None)
            
            for key, value in update_data.items():
                setattr(existing_profile, key, value)
            existing_profile.save()
            
            output_serializer = self.get_serializer(existing_profile)
            return Response({
                "success": True,
                "created": False,
                "updated": True,
                "data": output_serializer.data
            }, status=status.HTTP_200_OK)
        else:
            profile = serializer.save()
            output_serializer = self.get_serializer(profile)
            return Response({
                "success": True,
                "created": True,
                "updated": False,
                "data": output_serializer.data
            }, status=status.HTTP_201_CREATED)

    