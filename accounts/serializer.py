from rest_framework import serializers
from .models import ProfileModel


class ProfileModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileModel
        fields = ['telegram']



class ProfileCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileModel
        fields = ["tel_id", "telegram", "fname", "lname"]
        # جلوگیری از ValidationError زودهنگام روی telegram
        extra_kwargs = {
            "telegram": {"validators": []},
            "tel_id": {"validators": []}
        }

    def validate_tel_id(self, value):
        # tel_id شما CharField با طول 10 است؛ اگر همین را می‌خواهید enforce کنید:
        v = str(value)
        if not v.isdigit() or len(v) != 10:
            raise serializers.ValidationError("Invalid tel_id format")
        return v



class ProfileURDSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileModel
        fields = '__all__'

