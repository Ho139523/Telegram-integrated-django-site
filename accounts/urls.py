from django.urls import path
from .views import *
from django.contrib.auth import views

app_name = 'accounts'
urlpatterns = [

    path('login/', login.as_view(), name='login'),
    path('logout/', logout_user, name='logout'),
    path('signup/', signup_user, name='signup'),
    path('dashboard/<slug:username>/profile', profile, name="profile"),
    path('panel/<slug:username>/dashboard', profile, name="dashboard"),
    path('panel/<slug:username>/billing', profile, name="billing"),
    path('panel/<slug:username>/notifications', profile, name="notifications"),

    path('panel/<slug:username>/password-change', ChangePassword.as_view(), name="Change Password"),
    # path("password_change/done/", PasswordChangeDone.as_view(), name="password_change_done"),


    # path("login/", views.LoginView.as_view(), name="login"),
    # path("logout/", views.LogoutView.as_view(), name="logout"),
    
    # path("password_change/", views.PasswordChangeView.as_view(), name="password_change"),
    # path("password_change/done/", views.PasswordChangeDoneView.as_view(), name="password_change_done"),
    
    # path("password_reset/", views.PasswordResetView.as_view(), name="password_reset"),
    # path("password_reset/done/", views.PasswordResetDoneView.as_view(), name="password_reset_done",),
    # path("reset/<uidb64>/<token>/", views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    # path("reset/done/", views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),

]



