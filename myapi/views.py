from django.shortcuts import render

# Heart API
from rest_framework.generics import ListCreateAPIView
from heartpred.models import heart
from .serializer import HeartSerializer

# Shoe API
from rest_framework import viewsets
from products.serializer import ProductSerializer
from products.models import Product

# Check Telegram User Registration
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from accounts.models import ProfileModel
from accounts.serializer import ProfileModelSerializer
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import requests 



class HeartCreateAPIView(ListCreateAPIView):
    queryset = heart.objects.all()
    serializer_class = HeartSerializer



class ProductListView(APIView):
    def get(self, request):
        # دریافت کد محصول از پارامترهای کوئری
        code = request.query_params.get('code')  # استفاده از query_params یا request.GET
        if not code:
            return Response({"error": "Product code is required"}, status=400)

        try:
            # جستجوی محصول بر اساس کد
            product = Product.objects.get(code=code)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)

        # سریالایز کردن داده‌ها
        serializer = ProductSerializer(product)
        return Response(serializer.data)




 

@method_decorator(csrf_exempt, name='dispatch')
class CheckTelegramUserRegistrationView(APIView):

    def post(self, request):
        tel_id = request.data.get('tel_id')
        if not tel_id:
            return Response({"error": "tel_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        profile_exists = ProfileModel.objects.filter(tel_id=tel_id).exists()

        if profile_exists:
            return Response({
                "message": f"{tel_id} عزیز شما قبلا در ربات ثبت‌نام کرده‌اید."
            }, status=status.HTTP_200_OK)

        else:
            # اگر می‌خواهی کاربر جدید بسازی اینجا بساز
            # ProfileModel.objects.create(tel_id=tel_id, ...)
            return Response({
                "message": "ثبت‌نام شما با موفقیت انجام شد."
            }, status=status.HTTP_201_CREATED)

    def get(self, request):
        # بهتر است به کل متد GET را غیرمجاز اعلام کنی تا هر کس اشتباها GET زد بفهمد
        return Response({"detail": "Method GET not allowed. Please use POST."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
