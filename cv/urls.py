from django.urls import path
from .views import *

app_name='cv'
urlpatterns = [
    path('accounts/cv/', cv_view, name='cv'),
]

