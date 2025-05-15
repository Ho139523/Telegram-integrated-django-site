from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from .models import User, ProfileModel, Address
from django import forms
import pycountry


import requests
from django import forms
from .models import Address
import pycountry



import requests
from django import forms
from .models import Address
import pycountry



class CustomUserAdmin(UserAdmin):
    UserAdmin.fieldsets[2][1]['fields'] = ("is_active", "is_staff", "is_superuser", "special_user", "is_special_user_manual", "groups", "user_permissions")
    UserAdmin.fieldsets[1][1]['fields'] = ("first_name", "last_name", "email", "lang")

    list_display = UserAdmin.list_display + ('lang', 'is_special_user')

    search_fields = UserAdmin.search_fields + ('lang',)
    list_filter = UserAdmin.list_filter + ('lang',)  # فقط lang چون فیلد است



class AddressAdminForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = "__all__"

    shipping_country = forms.ChoiceField(
        choices=[("", "---------")] + [(c.alpha_2, c.name) for c in pycountry.countries if c.alpha_2 != "IL"],
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
        super().__init__(*args, **kwargs)

        self.province_code_to_name = {}
        self.city_code_to_name = {}

        country_code = self.data.get("shipping_country") or getattr(self.instance, "shipping_country", None)
        selected_province = self.data.get("shipping_province") or getattr(self.instance, "shipping_province", None)
        selected_city = self.data.get("shipping_city") or getattr(self.instance, "shipping_city", None)

        # ----- Province Setup -----
        province_choices = [("", "---------")]
        if country_code:
            try:
                url = f"http://api.geonames.org/searchJSON?country={country_code}&featureClass=A&featureCode=ADM1&maxRows=1000&lan=fa&username=Hussein2079"
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    for p in data.get("geonames", []):
                        code = p["adminCode1"]
                        name = p["name"]
                        province_choices.append((code, name))
                        self.province_code_to_name[code] = name
            except:
                pass

        if selected_province and all(p[0] != selected_province for p in province_choices):
            province_choices.append((selected_province, f"{selected_province} (Unknown)"))

        self.fields["shipping_province"].choices = province_choices

        # ----- City Setup -----
        city_choices = [("", "---------")]
        if country_code and selected_province:
            province_code = selected_province
            try:
                url = f"http://api.geonames.org/searchJSON?country={country_code}&adminCode1={province_code}&featureClass=P&maxRows=1000&lan=fa&username=Hussein2079"
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    for c in data.get("geonames", []):
                        code = str(c["geonameId"])
                        name = c["name"]
                        city_choices.append((code, name))
                        self.city_code_to_name[code] = name
            except:
                pass

        if selected_city and all(c[0] != selected_city for c in city_choices):
            city_choices.append((selected_city, f"{selected_city} (Unknown)"))

        self.fields["shipping_city"].choices = city_choices

    def clean(self):
        cleaned_data = super().clean()

        province_code = cleaned_data.get("shipping_province")
        city_code = cleaned_data.get("shipping_city")

        # Replace province code with name
        if province_code in self.province_code_to_name:
            cleaned_data["shipping_province"] = self.province_code_to_name[province_code]

        # Replace city code with name
        if city_code in self.city_code_to_name:
            cleaned_data["shipping_city"] = self.city_code_to_name[city_code]

        return cleaned_data

    class Media:
        js = ('admin/js/address_admin.js',)


class AddressAdmin(admin.ModelAdmin):
    form = AddressAdminForm



class ProfileModelAdmin(admin.ModelAdmin):
    list_display = ('user', 'lang')       # نمایش در جدول
    list_filter = ('lang',)   



admin.site.register(User, CustomUserAdmin)
admin.site.register(ProfileModel, ProfileModelAdmin)
admin.site.register(Address, AddressAdmin)
