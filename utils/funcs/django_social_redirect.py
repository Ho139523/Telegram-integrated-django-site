from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.contrib.auth import login as auth_login
from social_core.exceptions import AuthException
from social_django.models import UserSocialAuth
from django.contrib import messages

def custom_redirect(backend, user, response, *args, **kwargs):
    """
    Redirects the user to a URL containing their username after social login.
    """
    username = user.username  # Get the logged-in user's username
    return redirect(reverse("accounts:profile", kwargs={"username":username}))  # Redirect to a dynamic URL



def custom_complete(request, backend, *args, **kwargs):
    try:
        # Complete the login process
        user = request.backend.do_auth(request.GET.get('access_token'))
        
        if user and user.is_authenticated:
            auth_login(request, user)  # Log in the user
            
            # Redirect to a dynamic URL with the username
            username = user.username
            return redirect(reverse("accounts:profile", kwargs={"username": username}))
        else:
            messages.error(request, "Something went wrong with authentication!")
            return redirect("accounts:login")
            
    except AuthException as e:
        messages.error(request, "Authentication failed!")
        return redirect("accounts:login")
