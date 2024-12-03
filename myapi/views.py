from django.shortcuts import render

# Heart API
from rest_framework.generics import ListCreateAPIView
from heartpred.models import heart
from .serializer import HeartSerializer

# Shoe API
from rest_framework import viewsets
from products.serializer import ShoeSerializer
from products.models import ShoeModel

class HeartCreateAPIView(ListCreateAPIView):
    queryset = heart.objects.all()
    serializer_class = HeartSerializer


class ShoeView(viewsets.ModelViewSet):
    queryset = ShoeModel.objects.filter(stock=True)
    serializer_class = ShoeSerializer