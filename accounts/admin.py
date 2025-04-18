from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ProfileModel, Address
from django import forms
import pycountry


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

        country_code = self.data.get("shipping_country") or getattr(self.instance, "shipping_country", None)
        province_code = self.data.get("shipping_province") or getattr(self.instance, "shipping_province", None)
        city_code = self.data.get("shipping_city") or getattr(self.instance, "shipping_city", None)

        # Set province choices
        province_choices = [("", "---------")]
        if country_code:
            try:
                url = f"http://api.geonames.org/searchJSON?country={country_code}&featureClass=A&featureCode=ADM1&maxRows=1000&username=Hussein2079"
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    province_choices += [(p["adminCode1"], p["name"]) for p in data.get("geonames", [])]
            except:
                pass

        # If instance/provided province is not in choices, inject it manually
        if province_code and all(p[0] != province_code for p in province_choices):
            province_choices.append((province_code, f"{province_code} (Unknown)"))

        self.fields["shipping_province"].choices = province_choices

        # Set city choices
        city_choices = [("", "---------")]
        if country_code and province_code:
            try:
                url = f"http://api.geonames.org/searchJSON?country={country_code}&adminCode1={province_code}&featureClass=P&maxRows=1000&username=Hussein2079"
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    city_choices += [(str(c["geonameId"]), c["name"]) for c in data.get("geonames", [])]
            except:
                pass

        # If instance/provided city is not in choices, inject it manually
        if city_code and all(c[0] != str(city_code) for c in city_choices):
            city_choices.append((str(city_code), f"{city_code} (Unknown)"))

        self.fields["shipping_city"].choices = city_choices

    class Media:
        js = ('admin/js/address_admin.js',)



class AddressAdmin(admin.ModelAdmin):
    form = AddressAdminForm


admin.site.register(User, UserAdmin)
admin.site.register(ProfileModel)
admin.site.register(Address, AddressAdmin)
