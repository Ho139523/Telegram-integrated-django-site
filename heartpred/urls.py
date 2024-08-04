from django.urls import path
from .views import *

urlpatterns = [
    path('heart-prediction/', heartpred, name='heartpred'),
]

