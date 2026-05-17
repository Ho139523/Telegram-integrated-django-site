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



# accounts/serializers.py
from rest_framework import serializers
from accounts.models import ProfileModel


class BotProfileSerializer(serializers.ModelSerializer):
    """
    Comprehensive serializer for all bot CRUD operations
    Handles both Telegram (tel_id) and Bale (bale_id) profiles
    Can create profile with either identifier or both
    """
    
    class Meta:
        model = ProfileModel
        fields = [
            'id',
            'tel_id',
            'bale_id',
            'telegram',
            'bale',
            'fname',
            'lname',
            'phone',
            'lang',
            'avatar',
            'background_pic',
            'birthday',
            'about_me',
            'instagram',
            'tweeter',
            'credit',
            'user_level',
            'seller_mode',
            'tel_menu',
            'extra_button_menu',
            'settings_menu',
            'profile_menu',
            'store_menu',
            'server_store',
            'hidden_videos',
        ]
        read_only_fields = [
            'id',
            'credit',
            'user_level',
            'tel_menu',
            'extra_button_menu',
            'settings_menu',
            'profile_menu',
            'store_menu',
            'hidden_videos',
        ]
        extra_kwargs = {
            'tel_id': {'required': False, 'allow_blank': True, 'allow_null': True},
            'bale_id': {'required': False, 'allow_blank': True, 'allow_null': True},
            'telegram': {'required': False, 'allow_blank': True, 'allow_null': True},
            'bale': {'required': False, 'allow_blank': True, 'allow_null': True},
            'fname': {'required': False, 'allow_blank': True, 'allow_null': True},
            'lname': {'required': False, 'allow_blank': True, 'allow_null': True},
            'phone': {'required': False, 'allow_blank': True, 'allow_null': True},
            'lang': {'required': False, 'default': 'en'},
            'avatar': {'required': False},
            'background_pic': {'required': False},
            'birthday': {'required': False, 'allow_null': True},
            'about_me': {'required': False, 'allow_blank': True},
            'instagram': {'required': False, 'allow_blank': True},
            'tweeter': {'required': False, 'allow_blank': True},
            'seller_mode': {'required': False, 'default': False},
        }
    
    def _validate_platform_id(self, value, platform_name):
        """
        Generic validator for platform IDs (tel_id or bale_id)
        
        Args:
            value: The ID value to validate
            platform_name: 'tel_id' or 'bale_id' for error messages
        
        Returns:
            Validated value as string
        """
        if not value:
            return None
        
        value = str(value)
        
        # Check if contains only digits
        if not value.isdigit():
            raise serializers.ValidationError(f"{platform_name} must contain only digits")
        
        # Check length (between 5 and 20 digits)
        if len(value) < 5 or len(value) > 20:
            raise serializers.ValidationError(f"{platform_name} must be between 5 and 20 digits")
        
        return value
    
    def validate_tel_id(self, value):
        """Validate telegram ID format"""
        return self._validate_platform_id(value, "tel_id")
    
    def validate_bale_id(self, value):
        """Validate bale ID format"""
        return self._validate_platform_id(value, "bale_id")
    
    def validate_phone(self, value):
        """Validate phone number format (optional)"""
        if not value:
            return None
        
        value = str(value)
        if not value.isdigit():
            raise serializers.ValidationError("Phone number must contain only digits")
        
        if len(value) != 11 or not value.startswith('09'):
            raise serializers.ValidationError("Phone number must be 11 digits starting with 09")
        
        return value
    
    def validate_lang(self, value):
        """Validate language code"""
        if not value:
            return 'en'
        
        allowed_langs = ['en', 'fa', 'ar', 'zh', 'ru']
        if value not in allowed_langs:
            raise serializers.ValidationError(f"Language must be one of: {allowed_langs}")
        
        return value
    
    def validate(self, data):
        """
        Cross-field validation for both create and update operations
        
        Rules:
        - At least one of tel_id or bale_id must be provided (for create)
        - If both are provided, both must be valid
        - Check uniqueness for the specific platform ID
        - For update, only check the ID that is being changed
        """
        is_create = self.instance is None
        
        if is_create:
            # For create: at least one platform ID must be provided
            tel_id = data.get('tel_id')
            bale_id = data.get('bale_id')
            
            if not tel_id and not bale_id:
                raise serializers.ValidationError(
                    "Either tel_id or bale_id must be provided"
                )
            
            # Check uniqueness for tel_id (if provided)
            if tel_id:
                if ProfileModel.objects.filter(tel_id=tel_id).exists():
                    raise serializers.ValidationError(
                        {"tel_id": "A profile with this tel_id already exists"}
                    )
            
            # Check uniqueness for bale_id (if provided)
            if bale_id:
                if ProfileModel.objects.filter(bale_id=bale_id).exists():
                    raise serializers.ValidationError(
                        {"bale_id": "A profile with this bale_id already exists"}
                    )
        
        else:
            # For update: if we're changing an ID, check uniqueness (excluding self)
            tel_id = data.get('tel_id')
            bale_id = data.get('bale_id')
            
            if tel_id and tel_id != getattr(self.instance, 'tel_id', None):
                if ProfileModel.objects.filter(tel_id=tel_id).exists():
                    raise serializers.ValidationError(
                        {"tel_id": "A profile with this tel_id already exists"}
                    )
            
            if bale_id and bale_id != getattr(self.instance, 'bale_id', None):
                if ProfileModel.objects.filter(bale_id=bale_id).exists():
                    raise serializers.ValidationError(
                        {"bale_id": "A profile with this bale_id already exists"}
                    )
        
        return data
    
    def create(self, validated_data):
        """Create new profile with default values"""
        # Set default values if not provided
        if 'lang' not in validated_data:
            validated_data['lang'] = 'en'
        
        if 'seller_mode' not in validated_data:
            validated_data['seller_mode'] = False
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """
        Update existing profile without overwriting sensitive fields
        Also handles linking (partial updates)
        """
        # فیلدهایی که نباید در update تغییر کنند
        sensitive_fields = ['credit', 'user_level']
        
        for field in sensitive_fields:
            if field in validated_data and self.instance is not None:
                validated_data.pop(field)
        
        # اگر فقط یکی از IDها در update آمده باشد، فقط همان را به‌روز کن
        tel_id = validated_data.get('tel_id')
        bale_id = validated_data.get('bale_id')
        
        # اگر یک پلتفرم جدید اضافه می‌شود (مثلاً ادغام)
        if tel_id and not instance.tel_id:
            instance.tel_id = tel_id
            validated_data.pop('tel_id')
        
        if bale_id and not instance.bale_id:
            instance.bale_id = bale_id
            validated_data.pop('bale_id')
        
        return super().update(instance, validated_data)


class BotProfileCheckSerializer(serializers.Serializer):
    """
    Serializer for check endpoint - works with both tel_id and bale_id
    """
    tel_id = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=20)
    bale_id = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=20)
    
    def validate(self, data):
        """Ensure at least one identifier is provided"""
        tel_id = data.get('tel_id')
        bale_id = data.get('bale_id')
        
        if not tel_id and not bale_id:
            raise serializers.ValidationError(
                "Either tel_id or bale_id must be provided"
            )
        
        # Validate tel_id format if provided
        if tel_id:
            tel_id_str = str(tel_id)
            if not tel_id_str.isdigit():
                raise serializers.ValidationError(
                    {"tel_id": "tel_id must contain only digits"}
                )
            if len(tel_id_str) < 5 or len(tel_id_str) > 20:
                raise serializers.ValidationError(
                    {"tel_id": "tel_id must be between 5 and 20 digits"}
                )
            data['tel_id'] = tel_id_str
        
        # Validate bale_id format if provided
        if bale_id:
            bale_id_str = str(bale_id)
            if not bale_id_str.isdigit():
                raise serializers.ValidationError(
                    {"bale_id": "bale_id must contain only digits"}
                )
            if len(bale_id_str) < 5 or len(bale_id_str) > 20:
                raise serializers.ValidationError(
                    {"bale_id": "bale_id must be between 5 and 20 digits"}
                )
            data['bale_id'] = bale_id_str
        
        return data