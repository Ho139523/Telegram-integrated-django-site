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



from rest_framework import serializers
from .models import User, ProfileModel, Address

class UserSerializer(serializers.ModelSerializer):
    is_special_user = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'lang', 'is_special_user']


class AddressSerializer(serializers.ModelSerializer):
    shipping_country_name = serializers.ReadOnlyField()
    shipping_province_name = serializers.ReadOnlyField()
    shipping_city_name = serializers.ReadOnlyField()

    class Meta:
        model = Address
        fields = [
            'id', 'profile', 'shipping_line1', 'shipping_line2',
            'shipping_country', 'shipping_province', 'shipping_city',
            'shipping_zip_code', 'shipping_home_phone', 'shipping_is_active',
            'shipping_country_name', 'shipping_province_name', 'shipping_city_name'
        ]


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    active_address = serializers.SerializerMethodField()

    class Meta:
        model = ProfileModel
        fields = [
            'id', 'user', 'fname', 'lname', 'avatar', 'background_pic',
            'birthday', 'phone', 'about_me', 'instagram', 'tweeter', 'telegram',
            'credit', 'tel_id', 'tel_menu', 'extra_button_menu', 'seller_mode',
            'settings_menu', 'profile_menu', 'lang', 'server_store', 'hidden_videos',
            'user_level', 'active_address'
        ]
    
    def get_active_address(self, obj):
        address = obj.get_active_address()
        if address:
            return AddressSerializer(address).data
        return None


from rest_framework import serializers
from .models import User, ProfileModel

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'lang')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        # create profile
        ProfileModel.objects.get_or_create(user=user, tel_id=None, defaults={'lang': user.lang})
        return user
    




# accounts/serializers.py - اضافه کردن

class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating profile (all fields optional)
    """
    class Meta:
        model = ProfileModel
        fields = [
            'fname', 'lname', 'phone', 'avatar', 'background_pic',
            'birthday', 'about_me', 'instagram', 'tweeter', 'telegram',
            'lang', 'seller_mode', 'user_level'
        ]
        extra_kwargs = {
            'fname': {'required': False},
            'lname': {'required': False},
            'phone': {'required': False},
            'lang': {'required': False},
        }
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


