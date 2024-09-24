from .models import User
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django import forms
from .models import ProfileModel
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field



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
        fields = ['fname', 'lname', 'Phone', 'about_me', 'address', 'birthday', 'tweeter', 'instagram']
        
        widgets = {
                'about_me': forms.TextInput(attrs={"placeholder": "Describe yourself and let others know you better", 'class': 'form-control d-none', 'id': 'aboutmeField'}),
                'fname': forms.TextInput(attrs={"placeholder": "Type in your first name", 'class': 'form-control d-none', 'id': 'fnameField'}),
                'lname': forms.TextInput(attrs={"placeholder": "Type in your last name", 'class': 'form-control d-none', 'id': 'lnameField'}),
                'Phone': forms.TextInput(attrs={"placeholder": "Type in your phone number", 'class': 'form-control d-none', 'id': 'phoneField'}),
                'birthday': forms.TextInput(attrs={"placeholder": "Type in your birthday date", 'class': 'form-control d-none', 'id': 'birthdayField'}),
                'address': forms.TextInput(attrs={"placeholder": "Type in your address", 'class': 'form-control d-none', 'id': 'addressField'}),
                'tweeter': forms.TextInput(attrs={"placeholder": "Type in your Tweeter ID", 'class': 'form-control'}),
                'instagram': forms.TextInput(attrs={"placeholder": "Type in your Instagram", 'class': 'form-control'}),
            }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False
        self.helper.layout = Layout(
            Field('fname', css_class='form-control d-none', wrapper_class='col-6', id='fnameField'),
            Field('about_me', css_class='form-control d-none', wrapper_class='col-6', id='aboutmeField'),
            Field('lname', css_class='form-control d-none', wrapper_class='col-6', id='lnameField'),
            Field('Phone', css_class='form-control d-none', wrapper_class='col-6', id='phoneField'),
            Field('address', css_class='form-control d-none', wrapper_class='col-6', id='addressField'),
            Field('birthday', css_class='form-control d-none', wrapper_class='col-6'),
            Field('tweeter', css_class='form-control', wrapper_class='col-6', id='tweeterField'),
            Field('instagram', css_class='form-control', wrapper_class='col-6'),
        )
