from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from .models import User, ProfileModel, Address
from django import forms
import pycountry
from utils.funcs.geonames_address import get_country_choices, load_geodata, get_province_choices, get_city_choices
import requests





class CustomUserAdmin(UserAdmin):
    UserAdmin.fieldsets[2][1]['fields'] = ("is_active", "is_staff", "is_superuser", "special_user", "is_special_user_manual", "groups", "user_permissions")
    UserAdmin.fieldsets[1][1]['fields'] = ("first_name", "last_name", "email", "lang")

    list_display = UserAdmin.list_display + ('lang', 'is_special_user')

    search_fields = UserAdmin.search_fields + ('lang',)
    list_filter = UserAdmin.list_filter + ('lang',)



class AddressAdminForm(forms.ModelForm):
    
    shipping_country = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_country'})
    )


    shipping_province = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_province'})
    )

    shipping_city = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_city'})
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        self.lang = getattr(self.request.user, "lang", "en") if self.request else "en"
        super().__init__(*args, **kwargs)

        self.province_code_to_name = {}
        self.city_code_to_name = {}

        self.fields["shipping_country"].choices = [("", "---------")] + get_country_choices(self.lang)

        # آماده‌سازی انتخاب‌های اولیه
        country_code = self.data.get("shipping_country") or getattr(self.instance, "shipping_country", None)
        selected_province = self.data.get("shipping_province") or getattr(self.instance, "shipping_province", None)
        selected_city = self.data.get("shipping_city") or getattr(self.instance, "shipping_city", None)

        province_choices = [("", "---------")]
        city_choices = [("", "---------")]

        all_data = load_geodata()

        if country_code in all_data:
            provinces = all_data[country_code].get("provinces", {})
            for prov_code, prov_data in provinces.items():
                name = prov_data["names"].get(self.lang) or prov_data["names"].get("en") or prov_code
                province_choices.append((prov_code, name))
                self.province_code_to_name[prov_code] = name

            if selected_province in provinces:
                cities = provinces[selected_province].get("cities", {})
                for city_code, city_data in cities.items():
                    name = city_data["names"].get(self.lang) or city_data["names"].get("en") or city_code
                    city_choices.append((city_code, name))
                    self.city_code_to_name[city_code] = name

        if selected_province and all(p[0] != selected_province for p in province_choices):
            province_choices.append((selected_province, f"{selected_province} (Unknown)"))

        if selected_city and all(c[0] != selected_city for c in city_choices):
            city_choices.append((selected_city, f"{selected_city} (Unknown)"))

        self.fields["shipping_province"].choices = province_choices
        self.fields["shipping_city"].choices = city_choices

    # def clean(self):
    #     cleaned_data = super().clean()

    #     province_code = cleaned_data.get("shipping_province")
    #     city_code = cleaned_data.get("shipping_city")

    #     if province_code in self.province_code_to_name:
    #         cleaned_data["shipping_province"] = self.province_code_to_name[province_code]

    #     if city_code in self.city_code_to_name:
    #         cleaned_data["shipping_city"] = self.city_code_to_name[city_code]

    #     return cleaned_data

    class Meta:
        model = Address
        fields = "__all__"

    class Media:
        js = ('admin/js/address_admin.js',)



class AddressAdmin(admin.ModelAdmin):
    form = AddressAdminForm

    def get_form(self, request, obj=None, **kwargs):
        Form = super().get_form(request, obj, **kwargs)
        class FormWithRequest(Form):
            def __init__(self2, *args, **kw):
                kw['request'] = request
                super().__init__(*args, **kw)
        return FormWithRequest


################# profile

from django.contrib.admin import SimpleListFilter

class PlatformFilter(SimpleListFilter):
    title = 'Platform'
    parameter_name = 'platform'
    
    def lookups(self, request, model_admin):
        return (
            ('telegram', 'Telegram Only'),
            ('bale', 'Bale Only'),
            ('both', 'Telegram + Bale'),
            ('site', 'Website Only'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'telegram':
            return queryset.filter(tel_id__isnull=False, bale_id__isnull=True)
        if self.value() == 'bale':
            return queryset.filter(bale_id__isnull=False, tel_id__isnull=True)
        if self.value() == 'both':
            return queryset.filter(tel_id__isnull=False, bale_id__isnull=False)
        if self.value() == 'site':
            return queryset.filter(user__isnull=False, tel_id__isnull=True, bale_id__isnull=True)
        return queryset


class ProfileModelAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'lang', 'platform', 'created_at')
    list_filter = ('lang', PlatformFilter)
    search_fields = ('tel_id', 'bale_id', 'user__username', 'fname', 'lname', 'phone')
    readonly_fields = ('tel_id', 'bale_id', 'user', 'created_at', 'updated_at')
    
    def display_name(self, obj):
        """
        نمایش نام کاربر با شناسه پلتفرم مربوطه
        اولویت: user.username > (fname + lname) > شناسه پلتفرم
        """
        # اگر کاربر متصل به سایت دارد
        if obj.user:
            return f"{obj.user.username} (User)"
        
        # اگر نام و نام خانوادگی دارد
        if obj.fname or obj.lname:
            full_name = f"{obj.fname or ''} {obj.lname or ''}".strip()
            if obj.tel_id:
                return f"{full_name} - Telegram: {obj.tel_id}"
            elif obj.bale_id:
                return f"{full_name} - Bale: {obj.bale_id}"
            return full_name
        
        # فقط شناسه پلتفرم
        if obj.tel_id:
            return f"Telegram User: {obj.tel_id}"
        elif obj.bale_id:
            return f"Bale User: {obj.bale_id}"
        
        return "Unnamed User"
    
    display_name.short_description = "User Name / Platform ID"
    
    def platform(self, obj):
        """
        نمایش پلتفرم فعال کاربر
        """
        if obj.tel_id and obj.bale_id:
            return "Telegram + Bale"
        elif obj.tel_id:
            return "Telegram"
        elif obj.bale_id:
            return "Bale"
        return "Unknown"
    
    platform.short_description = "Platform"
    
    def created_at(self, obj):
        """نمایش تاریخ ایجاد (اگر فیلد دارید)"""
        return obj.date_joined if hasattr(obj, 'date_joined') else None
    
    created_at.short_description = "Created"
    
    created_at.empty_value_display = "-"
    
    def updated_at(self, obj):
        """نمایش تاریخ بروزرسانی (اگر فیلد دارید)"""
        return None  # اگر فیلد updated_at دارید، اینجا قرار دهید
    
    updated_at.short_description = "Updated"
admin.site.register(User, CustomUserAdmin)
admin.site.register(ProfileModel, ProfileModelAdmin)
admin.site.register(Address, AddressAdmin)
