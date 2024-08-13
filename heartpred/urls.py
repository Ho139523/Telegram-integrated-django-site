from django.urls import path
from .views import *

app_name="heartpred"
urlpatterns = [
    path('', heartpredformshow, name='heartpred'),
    path("predict/", heartpred, name="prediction"),
]

