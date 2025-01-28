from django.urls import path, include

# Heart API
from .views import HeartCreateAPIView, CheckTelegramUserRegistrationView#, ShoeView
from myapi.views import ProductListView

# Shoe API
# from rest_framework import routers

# router = routers.DefaultRouter()
# router.register("", ShoeView)

urlpatterns = [
    # Heart API
    path("heartrecords/", HeartCreateAPIView.as_view()),
    path('products/', ProductListView.as_view(), name='product-list'),
    # Shoe API
    #path('', ShoeView.as_view({'get': 'list'})),
    # path('check-registration/', CheckTelegramUserRegistrationView.as_view())

]