from .views import HeartCreateAPIView
from django.urls import path, include

urlpatterns = [
    path("", HeartCreateAPIView.as_view()),
]
