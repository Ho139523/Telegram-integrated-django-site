from .models import User
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django import forms
from .models import ProfileModel, ShippingAddressModel
from django.forms import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field
from utils.variables.countries import countries

import pycountry


error_messages_email = {
    'required': 'please Fill-out this field',
    'invalid': 'invalid format for email',
    'max_length': 'max length is 40 chars',
}



class SignUpForm(UserCreationForm):
    email=forms.EmailField(error_messages=error_messages_email, max_length=40)
    
    class Meta:
        model=User
        fields=("username", "email", "password1", "password2")
        
        
        
class PasswordResetFormChanged(PasswordResetForm):
    Last_changed=forms.DateTimeField()
    
    def __init__(self, *args, **kwargs):

        super(PasswordResetFormChanged, self).__init__(*args, **kwargs)
        today = datetime.date.now()
        self.fields["Last_changed"].initial = today
        
        
class HeaderImageForm(forms.ModelForm):
    class Meta:
        model = ProfileModel
        fields = ['background_pic']  # Make sure your Profile model has this field
        widgets = {
            'background_pic': forms.FileInput(attrs={'accept': 'image/*'}),
        }
        
class AvatarImageForm(forms.ModelForm):
    class Meta:
        model = ProfileModel
        fields = ['avatar']  # Make sure your Profile model has this field
        widgets = {
            'avatar': forms.FileInput(attrs={'accept': 'image/*'}),
        }
    
    
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = ProfileModel
        fields = ['fname', 'lname', 'Phone', 'about_me', 'birthday', 'tweeter', 'instagram']
        
        widgets = {
                'about_me': forms.TextInput(attrs={"placeholder": "Describe yourself and let others know you better", 'class': 'form-control d-none', 'id': 'aboutmeField'}),
                'fname': forms.TextInput(attrs={"placeholder": "Type in your first name", 'class': 'form-control'}),
                'lname': forms.TextInput(attrs={"placeholder": "Type in your last name", 'class': 'form-control'}),
                'Phone': forms.TextInput(attrs={"placeholder": "Type in your phone number", 'class': 'form-control d-none', 'id': 'phoneField'}),
                'birthday': forms.TextInput(attrs={"placeholder": "Type in your birthday date", 'class': 'form-control d-none', 'id': 'birthdayField'}),
                # 'address': forms.TextInput(attrs={"placeholder": "Type in your address", 'class': 'form-control d-none', 'id': 'addressField'}),
                'tweeter': forms.TextInput(attrs={"placeholder": "Type in your Tweeter ID", 'class': 'form-control'}),
                'instagram': forms.TextInput(attrs={"placeholder": "Type in your Instagram", 'class': 'form-control',}),
            }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False
        self.helper.layout = Layout(
            Field('fname', css_class='form-control', wrapper_class='col-6'),
            Field('about_me', css_class='form-control d-none', wrapper_class='col-6', id='aboutmeField'),
            Field('lname', css_class='form-control', wrapper_class='col-6'),
            Field('Phone', css_class='form-control d-none', wrapper_class='col-6', id='phoneField'),
            # Field('address', css_class='form-control d-none', wrapper_class='col-6', id='addressField'),
            Field('birthday', css_class='form-control d-none', wrapper_class='col-6'),
            Field('tweeter', css_class='form-control', wrapper_class='col-6', id='tweeterField'),
            Field('instagram', css_class='form-control', wrapper_class='col-6'),
        )




class ShippingAddressForm(forms.ModelForm):
    shipping_country = forms.ChoiceField(choices=countries, widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_shipping_country'}))
    shipping_province = forms.ChoiceField(choices=[], required=False,widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_shipping_province'}))

    class Meta:
        model = ShippingAddressModel
        exclude = ['profile']

        widgets = {
            'shipping_line1': forms.TextInput(attrs={'class': 'textinput form-control', 'placeholder': 'Address Line 1', 'onfocus': 'focused(this)', 'onfocusout': 'defocused(this)', 'id': 'id_shipping_line1',  'name': 'shipping_line1'}),
            'shipping_line2': forms.TextInput(attrs={'class': 'textinput form-control', 'placeholder': 'Address Line 2', 'onfocus': 'focused(this)', 'onfocusout': 'defocused(this)', 'id': 'id_shipping_line2',  'name': 'shipping_line2'}),
            'shipping_city': forms.TextInput(attrs={'class': 'textinput form-control', 'placeholder': 'City', 'onfocus': 'focused(this)', 'onfocusout': 'defocused(this)', 'id': 'id_shipping_city',  'name': 'shipping_city'}),
            'shipping_country': forms.TextInput(attrs={'class': 'textinput form-control', 'placeholder': 'Country', 'onfocus': 'focused(this)', 'onfocusout': 'defocused(this)', 'id': 'id_shipping_country',  'name': 'shipping_country'}),
            'shipping_province': forms.TextInput(attrs={'class': 'textinput form-control', 'placeholder': 'Province', 'onfocus': 'focused(this)', 'onfocusout': 'defocused(this)', 'id': 'id_shipping_province',  'name': 'shipping_province'}),
            'shipping_zip': forms.TextInput(attrs={'class': 'textinput form-control', 'placeholder': 'Zip Code', 'onfocus': 'focused(this)', 'onfocusout': 'defocused(this)', 'id': 'id_shipping_zip',  'name': 'shipping_zip'}),
            'shipping_home_phone': forms.TextInput(attrs={'class': 'textinput form-control', 'placeholder': 'Home Phone Number', 'onfocus': 'focused(this)', 'onfocusout': 'defocused(this)', 'id': 'id_shipping_home_phone',  'name': 'shipping_home_phone'}),
        }
        
        
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        instance = kwargs.get('instance')
        country_code = instance.shipping_country if instance else None
        
        # Update province choices based on initial country selection
        if country_code:
            self.update_province_choices(country_code)

        # Crispy Forms helper
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('shipping_line1', wrapper_class='form-group'),
            Field('shipping_line2', wrapper_class='form-group'),
            Field('shipping_city', wrapper_class='form-group'),
            Field('shipping_zip', wrapper_class='form-group'),
            Field('shipping_country', wrapper_class='form-group'),
            Field('shipping_province', wrapper_class='form-group'),
        )
        
    def update_province_choices(self, country_code):
        """Update the province choices based on the selected country."""
        provinces = [(subdivision.code, subdivision.name) for subdivision in pycountry.subdivisions if subdivision.country_code == country_code]
        self.fields['shipping_province'].choices = provinces

    class Media:
        js = ('https://code.jquery.com/jquery-3.6.0.min.js', 'registration/dashboard/assets/js/province.js')

