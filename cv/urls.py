from django.urls import path
from .views import *

urlpatterns = [
    path('', cv_view, name='cv'),
]

