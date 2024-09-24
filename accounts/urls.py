from django.urls import path, re_path
from .views import *
from django.contrib.auth import views
from utils.funcs.django_social_redirect import custom_complete

app_name = 'accounts'
urlpatterns = [

    #login and logout
    path('login/', login.as_view(), name='login'),
    path('logout/', logout_user, name='logout'),
    path('socials/complete/google-oauth2/', custom_complete, name="custom_complete"),
    
    #signup
    path('signup/', signup_user, name='signup'),
    path('activate/<uidb64>/<token>/', activate, name='activate'),
    
    #profile
    path('panel/<slug:username>/profile', profile, name="profile"),
    path('panel/<slug:username>/dashboard', profile, name="dashboard"),
    path('panel/<slug:username>/billing', billing, name="billing"),
    path('panel/<slug:username>/notifications', profile, name="notifications"),

    #change password
    path('panel/<slug:username>/password-change', ChangePassword.as_view(), name="Change Password"),
    
    #reset password
    path("password_reset/", PasswordReset.as_view(), name="password_reset"),
    path("reset/<uidb64>/<token>/", PasswordResetConfirm.as_view(), name="password_reset_confirm"),
    
    #header and avatar image uploading
    path('panel/change-header-image/', change_header_image, name='change_header_image'),
    path('panel/change-avatar-image/', change_avatar_image, name='change_avatar_image'),
    path('panel/change-profile-data/', profile_update_view, name='change_profile_data'),


]



