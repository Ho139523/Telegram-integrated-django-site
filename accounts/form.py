from .models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms


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