from django.urls import path, re_path
from .views import *


app_name = 'payment'
urlpatterns = [
    # payment request
    path('request', send_request, name='request'),
    
    # payment verify
    path('verify', verify, name='verify'),
]
