from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms


class SignUpForm(UserCreationForm):
    email=forms.EmailField()
    username=forms.CharField(max_length=30)
    password1=forms.CharField(max_length=16, widget=forms.PasswordInput)
    password2=forms.CharField(max_length=16, widget=forms.PasswordInput)
    
    class Meta:
        model=User
        fields='__all__'