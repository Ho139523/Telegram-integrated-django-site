from django.shortcuts import render
from rest_framework.generics import CreateAPIView
from heartpred.models import heart
from .serializer import HeartSerializer

class HeartCreateAPIView(CreateAPIView):
    query_set = heart.objects.all()
    serializer_class = HeartSerializer
