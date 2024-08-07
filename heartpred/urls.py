from django.urls import path
from .views import *

app_name="heartpred"
urlpatterns = [
    path('', heartpred, name='heartpred'),
]

