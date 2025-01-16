from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ProfileModel
from django import forms
from .form import ShippingAddressForm



class ShippingAddressAdmin(admin.ModelAdmin):
    form = ShippingAddressForm
    UserAdmin.list_display += ("is_special_user",)
    UserAdmin.fieldsets[2][1]["fields"]= (
        "is_active",
        "is_staff",
        "is_superuser",
        "special_user",
        "groups",
        "user_permissions",
    )
                
    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == 'shipping_province':
            # Get the instance of the object being edited (if applicable)
            obj_id = request.resolver_match.kwargs.get('object_id')
            instance = self.get_object(request, obj_id)

            # Check if there's a country set on the instance and populate province choices
            if instance and instance.shipping_country:
                country_code = instance.shipping_country
                provinces = [(subdivision.code, subdivision.name) for subdivision in pycountry.subdivisions if subdivision.country_code == country_code]
                kwargs['choices'] = provinces
        return super().formfield_for_choice_field(db_field, request, **kwargs)




admin.site.register(User, UserAdmin)

admin.site.register(ProfileModel)
