from django.urls import path, re_path
from .views import *


app_name = 'payment'
urlpatterns = [
    # payment request
    path('payment/', views.payment_request, name='payment_request'),
    
    # payment verify
    path('verify/', views.payment_verify, name='payment_verify'),
]
