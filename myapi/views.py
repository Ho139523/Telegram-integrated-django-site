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



# aiobot hmac authentication for profile creation
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from accounts.serializer import ProfileCreateSerializer
from accounts.models import ProfileModel
from aiobot.auth import BotSignaturePermission

import traceback
from django.db import transaction, IntegrityError




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
            # ProfileModel.objects.create(tel_id=tel_id)
            return Response({
                "message": "ثبت‌نام شما با موفقیت انجام شد."
            }, status=status.HTTP_201_CREATED)

    def get(self, request):
        # بهتر است به کل متد GET را غیرمجاز اعلام کنی تا هر کس اشتباها GET زد بفهمد
        return Response({"detail": "Method GET not allowed. Please use POST."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)



class BotCreateProfileView(APIView):
    permission_classes = [BotSignaturePermission]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        ser = ProfileCreateSerializer(data=request.data)
        if not ser.is_valid():
            # ولیدیشن‌های فرمت/فیلدهای اجباری
            return Response(
                {"ok": False, "error": "invalid_payload", "details": ser.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = ser.validated_data
        tel_id = data["tel_id"]
        telegram = data.get("telegram")

        try:
            # اول: اگر پروفایل با این tel_id قبلاً هست → 409 به معنای «وجود دارد»
            existing = ProfileModel.objects.filter(tel_id=tel_id).first()
            if existing:
                # اگر خواستید اینجا فیلدها را به‌روزرسانی کنید (اختیاری):
                # در صورت تغییر telegram، قبل از ذخیره مطمئن شوید با دیگری conflict نمی‌کند.
                changes = {}
                for f in ("telegram", "fname", "lname"):
                    if f in data and data[f] is not None and getattr(existing, f) != data[f]:
                        changes[f] = data[f]

                if "telegram" in changes:
                    if ProfileModel.objects.filter(telegram=changes["telegram"]).exclude(pk=existing.pk).exists():
                        return Response(
                            {"created": False, "detail": "این Telegram قبلاً برای کاربر دیگری ثبت شده است."},
                            status=status.HTTP_409_CONFLICT,
                        )

                if changes:
                    for k, v in changes.items():
                        setattr(existing, k, v)
                    existing.save(update_fields=list(changes.keys()))

                out = ProfileCreateSerializer(existing).data
                return Response(
                    {"created": False, "detail": "کاربر از قبل وجود داشته است.", "profile": out},
                    status=status.HTTP_409_CONFLICT,
                )

            # دوم: اگر وجود نداشت، بسازیم؛ اما قبلش conflict تلگرام را چک کنیم
            if telegram and ProfileModel.objects.filter(telegram=telegram).exists():
                return Response(
                    {"created": False, "detail": "این Telegram قبلاً برای کاربر دیگری ثبت شده است."},
                    status=status.HTTP_409_CONFLICT,
                )

            profile = ProfileModel.objects.create(**data)
            out = ProfileCreateSerializer(profile).data
            # مطابق خواسته‌ی شما: «اگر ساخته شد ⇒ 200»
            return Response(
                {"created": True, "detail": "کاربر ایجاد شد.", "profile": out},
                status=status.HTTP_200_OK,
            )

        except IntegrityError as e:
            # اگر یکتایی دیتابیس خطا داد (به‌عنوان fallback)
            return Response(
                {"ok": False, "error": "integrity_error", "detail": str(e)},
                status=status.HTTP_409_CONFLICT,
            )
        except Exception as e:
            return Response(
                {"ok": False, "error": "server_error", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


from rest_framework import generics
from accounts.serializer import ProfileURDSerializer

class ProfileURDView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProfileModel.objects.all()
    serializer_class = ProfileURDSerializer
    lookup_field = 'tel_id'