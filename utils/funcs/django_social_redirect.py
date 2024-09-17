from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.contrib.auth import login as auth_login
from social_core.exceptions import AuthException
from social_django.models import UserSocialAuth
from django.contrib import messages
from accounts.models import User  # Django's User model
from django.contrib.auth import load_backend



def custom_complete(backend, user=None, response=None, *args, **kwargs):
    try:
        request = kwargs['request']

        if user is None:
            email = response.get('email')
            username = response.get('email').split('@')[0]

            user, created = User.objects.get_or_create(
                email=email,
                defaults={'username': username}
            )

            if created:
                user.first_name = response.get('given_name')
                user.last_name = response.get('family_name')
                user.set_unusable_password()
                user.save()

        if user and user.is_authenticated:
            # Attach the backend explicitly
            backend_path = 'social_core.backends.google.GoogleOAuth2'
            user.backend = backend_path
            auth_login(request, user, backend=backend_path)

            return redirect(reverse("accounts:profile", kwargs={"username": user.username}))
        else:
            messages.error(request, "Authentication failed!")
            return redirect("accounts:login")

    except AuthException as e:
        messages.error(request, f"Authentication failed: {str(e)}")
        return redirect("accounts:login")

    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect("accounts:login")

