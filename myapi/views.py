from django.shortcuts import render

# Heart API
from rest_framework.generics import ListCreateAPIView
from heartpred.models import heart
from .serializer import HeartSerializer

# Shoe API
from rest_framework import viewsets
#from products.serializer import ShoeSerializer
#from products.models import ShoeModel

# Check Telegram User Registration
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from telbot.models import telbotid
from accounts.models import ProfileModel
from accounts.serializer import ProfileModelSerializer
from telbot.serializer import TelbotidSerializer
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt



class HeartCreateAPIView(ListCreateAPIView):
    queryset = heart.objects.all()
    serializer_class = HeartSerializer


#class ShoeView(viewsets.ModelViewSet):
#    queryset = ShoeModel.objects.filter(stock=True)
#    serializer_class = ShoeSerializer
    

@method_decorator(csrf_exempt, name='dispatch')
class CheckTelegramUserRegistrationView(APIView):
    def post(self, request):
        tel_id = request.data.get('tel_id')
        print(tel_id)
        
        # Check if the user exists in telbotid or ProfileModel
        telbotid_exists = telbotid.objects.filter(tel_id=tel_id).values_list('tel_id')
        
        profile_exists = ProfileModel.objects.filter(telegram=tel_id).values_list('telegram')
        

        if tel_id in telbotid_exists | tel_id in profile_exists:
            return Response({
                "message": f"{tel_id} عزیز شما قبلا در ربات ثبت‌نام کرده‌اید."
            }, status=status.HTTP_200_OK)
            if tel_id not in telbotid_exists:
                new_telbotid = telbotid.objects.create(user=None, tel_id=tel_id)
                new_telbotid.save()
        else:
            # Create a new telbotid instance
            new_telbotid = telbotid.objects.create(user=None, tel_id=tel_id)
            new_telbotid.save()
            return Response({
                "message": "ثبت‌نام شما با موفقیت انجام شد."
            }, status=status.HTTP_201_CREATED)