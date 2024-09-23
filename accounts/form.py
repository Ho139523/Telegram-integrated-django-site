from .models import User
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django import forms
from .models import ProfileModel


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
    