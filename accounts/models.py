from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import pycountry
from django.core.validators import MinLengthValidator, int_list_validator
from django.utils.translation import gettext_lazy as _
import json
from django.utils.translation import get_language
from django.conf import settings
from django.db.models import Q


class User(AbstractUser):
    def get_language_choices():
        languages = []
        for lang in pycountry.languages:
            if hasattr(lang, 'alpha_2'):
                languages.append((lang.alpha_2, lang.name))
        return sorted(languages, key=lambda x: x[1])

    special_user = models.DateTimeField(default=timezone.now)
    is_special_user_manual = models.BooleanField(default=False)  # ✅ فیلد واقعی

    LANG_CHOICES = get_language_choices()

    lang = models.CharField(
        max_length=10,
        choices=LANG_CHOICES,
        default='fa',
        null=False,
        blank=True,
        verbose_name=_("Language")
    )

    @property
    def is_special_user(self):
        """
        کاربر special است اگر:
        - یا زمان ویژه بودنش هنوز تمام نشده
        - یا دستی علامت‌گذاری شده باشد
        """
        return self.special_user > timezone.now() or self.is_special_user_manual

    is_special_user.fget.boolean = True
    is_special_user.fget.short_description = "Special User"

    def save(self, *args, **kwargs):
        self.username = self.username.strip().lower()
        super().save(*args, **kwargs)

        # Sync language to ProfileModel
        if hasattr(self, 'profilemodel'):
            profile = self.profilemodel
            if profile.lang != self.lang:
                profile.lang = self.lang
                profile.save(update_fields=['lang'])

    def get_by_natural_key(self, username):
        return self.__class__.objects.get(username__iexact=username.strip())



class ProfileModel(models.Model):

    # ----------------------------
    # Language choices
    # ----------------------------
    def get_language_choices():
        languages = []
        for lang in pycountry.languages:
            if hasattr(lang, 'alpha_2'):
                languages.append((lang.alpha_2, lang.name))
        return sorted(languages, key=lambda x: x[1])

    # ----------------------------
    # Default Menus (keys only)
    # ----------------------------
    def default_tel_menu():
        return ["menu_balance", "menu_buy_by_code", "menu_categories", "menu_support", "menu_settings"]

    def default_extra_button_menu():
        return ["menu_cart"]

    def default_settings_menu():
        return ["menu_become_seller", "menu_my_address", "menu_profile", "menu_store"]

    def default_profile_menu():
        return ["menu_language"]
    
    def default_store_menu():
        return ["menu_language"]

    def get_default_store():
        from products.models import Store  # import inside function to avoid circular import
        try:
            return Store.objects.get(name="Intelleum").pk
        except Store.DoesNotExist:
            return None  # fallback, so migrations won't break

    # ----------------------------
    # Fields
    # ----------------------------
    user = models.OneToOneField(User, unique=True, null=True, on_delete=models.SET_NULL, blank=True)
    fname = models.CharField(max_length=100, blank=True, null=True, verbose_name="First Name")
    lname = models.CharField(max_length=150, blank=True, null=True, verbose_name="Last Name")
    avatar = models.ImageField(
        default="registration/user_avatars/default-avatar.png",
        upload_to="registration/user_avatars"
    )
    background_pic = models.ImageField(
        default="registration/user_headers/default_header.avif",
        upload_to="registration/user_headers",
        verbose_name="Header Image"
    )
    birthday = models.DateField(blank=True, null=True)
    phone = models.CharField(
        max_length=11,
        blank=True,
        null=True,
        verbose_name="Phone Number"
    )
    about_me = models.TextField(
        max_length=1000,
        blank=True,
        null=True,
        default="Describe yourself, your capabilities and talents here. Let others know how awesome you are ;)",
        verbose_name="About Me"
    )
    instagram = models.CharField(max_length=120, blank=True, null=True, verbose_name="Instagram ID")
    tweeter = models.CharField(max_length=120, blank=True, null=True, verbose_name="Tweeter ID")
    telegram = models.CharField(max_length=120, blank=True, null=True, verbose_name="Telegram ID")
    bale = models.CharField(max_length=120, blank=True, null=True, verbose_name="Bale ID")
    credit = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=False, blank=True)
    tel_id = models.CharField(
        max_length=20,
        validators=[int_list_validator(sep=''), MinLengthValidator(5)],
        unique=True,
        null=True,
        blank=True
    )
    bale_id = models.CharField(
        max_length=20,
        validators=[int_list_validator(sep=''), MinLengthValidator(5)],
        unique=True,
        null=True,
        blank=True
    )
    tel_menu = models.JSONField(default=default_tel_menu, blank=True, null=False)
    extra_button_menu = models.JSONField(default=default_extra_button_menu, blank=True, null=False)
    seller_mode = models.BooleanField(default=False, blank=False, null=False)
    settings_menu = models.JSONField(default=default_settings_menu, blank=True, null=False)
    profile_menu = models.JSONField(default=default_profile_menu, blank=True, null=False)
    store_menu = models.JSONField(default=default_store_menu, blank=True, null=False)
    lang = models.CharField(
        max_length=10,
        choices=get_language_choices(),
        default='en',
        unique=False,
        null=False,
        blank=True
    )
    # The store this profile is currently "connected" to (for browsing/buying).
    server_store = models.ForeignKey(
        "products.Store",
        on_delete=models.SET_NULL,
        default=get_default_store,
        null=True,
        blank=False,
        related_name="connected_profiles",
        verbose_name="Server Store"
    )
    hidden_videos = models.JSONField(default=dict)

    # -------------------------
    # helper methods for hidden_videos
    # -------------------------
    def is_video_hidden(self, command: str) -> bool:
        """بررسی می‌کند آیا کاربر این command را مخفی کرده یا نه."""
        try:
            return bool(self.hidden_videos.get(command))
        except Exception:
            return False

    def hide_video(self, command: str):
        """
        علامت‌گذاری یک command به عنوان 'مخفی'.
        از transaction و select_for_update برای جلوگیری از race استفاده می‌کنیم.
        """
        from django.db import transaction
        with transaction.atomic():
            # lock this profile row to avoid concurrent writes
            p = ProfileModel.objects.select_for_update().get(pk=self.pk)
            data = dict(p.hidden_videos or {})
            data[command] = True
            p.hidden_videos = data
            p.save(update_fields=['hidden_videos'])

    def unhide_video(self, command: str):
        with transaction.atomic():
            p = ProfileModel.objects.select_for_update().get(pk=self.pk)
            data = dict(p.hidden_videos or {})
            if command in data:
                data.pop(command)
                p.hidden_videos = data
                p.save(update_fields=['hidden_videos'])

    def clear_hidden_videos(self):
        with transaction.atomic():
            p = ProfileModel.objects.select_for_update().get(pk=self.pk)
            p.hidden_videos = {}
            p.save(update_fields=['hidden_videos'])

    # ----------------------------
    # Address helper
    # ----------------------------
    def get_active_address(self):
        return self.addresses.filter(shipping_is_active=True).first()

    # ----------------------------
    # User Levels
    # ----------------------------
    class UserLevel(models.TextChoices):
        BLUE = 'blue', 'Blue User'
        GREEN = 'green', 'Green User'
        SILVER = 'silver', 'Silver User'
        GOLD = 'gold', 'Golden User'

    user_level = models.CharField(
        max_length=10,
        choices=UserLevel.choices,
        default=UserLevel.BLUE
    )

    LEVEL_MENUS = {
        'blue': [
            ["menu_balance", "menu_buy_by_code", "menu_categories", "menu_support", "menu_settings"],
            ["menu_cart"],
            ["menu_become_seller", "menu_my_address", "menu_profile"],
            ["menu_language"],
            ["menu_language"],
        ],
        'green': [
            ["menu_balance", "menu_buy_by_code", "menu_categories", "menu_support", "menu_settings"],
            ["menu_cart"],
            ["menu_become_seller", "menu_my_address", "menu_profile"],
            ["menu_language"],
            ["menu_language"],
        ],
        'silver': [
            ["menu_balance", "menu_quick_buy", "menu_support"],
            ["menu_cart"],
            ["menu_become_seller", "menu_my_address", "menu_profile"],
            ["menu_language"],
            ["menu_language"],
        ],
        'gold': [
            ["menu_financial_report", "menu_advanced_buy", "menu_analytics"],
            ["menu_cart"],
            ["menu_become_seller", "menu_my_address", "menu_profile"],
            ["menu_language"],
            ["menu_language"],
        ],
        'seller': [
            ["product", "category", "menu_financial_report", "menu_analytics", "menu_settings"],
            ["menu_sale_statistics"],
            ["menu_back_to_buyer", "menu_change_warehouse", "menu_profile", "menu_store"],
            ["menu_language"],
            ["menu_language"],
        ],
    }

    def __str__(self):
        if self.user:
            return f"{self.user.username}  -  {self.tel_id}"
        return f"{self.fname} {self.lname}  -  {self.tel_id if self.tel_id else self.bale_id}"

    @property
    def age(self):
        if self.birthday:
            today = timezone.now().date()
            return today.year - self.birthday.year - (
                (today.month, today.day) < (self.birthday.month, self.birthday.day)
            )
        return None

    def save(self, *args, **kwargs):
        from utils.variables.translate import translations

        def translate_menu_keys(menu_keys):
            """ فقط کلیدها رو نگه دار، ترجمه تو send_menu انجام میشه """
            return list(menu_keys)  # copy

        if not self.pk:
            # پروفایل جدید
            self.tel_menu = translate_menu_keys(self.LEVEL_MENUS[self.user_level][0])
            self.extra_button_menu = translate_menu_keys(self.LEVEL_MENUS[self.user_level][1])
            self.settings_menu = translate_menu_keys(self.LEVEL_MENUS[self.user_level][2])
            self.profile_menu = translate_menu_keys(self.LEVEL_MENUS[self.user_level][3])
            self.store_menu = translate_menu_keys(self.LEVEL_MENUS[self.user_level][4])

        else:
            # پروفایل موجود
            old_instance = ProfileModel.objects.get(pk=self.pk)

            # تغییر سطح کاربری
            if old_instance.user_level != self.user_level and self.user_level in self.LEVEL_MENUS:
                self.tel_menu = translate_menu_keys(self.LEVEL_MENUS[self.user_level][0])
                self.extra_button_menu = translate_menu_keys(self.LEVEL_MENUS[self.user_level][1])
                self.settings_menu = translate_menu_keys(self.LEVEL_MENUS[self.user_level][2])
                self.profile_menu = translate_menu_keys(self.LEVEL_MENUS[self.user_level][3])
                self.store_menu = translate_menu_keys(self.LEVEL_MENUS[self.user_level][4])

            # تغییر حالت فروشنده
            if old_instance.seller_mode != self.seller_mode:
                if self.seller_mode:
                    # ورود به حالت فروشنده
                    self.tel_menu = translate_menu_keys(self.LEVEL_MENUS["seller"][0])
                    self.extra_button_menu = translate_menu_keys(self.LEVEL_MENUS["seller"][1])
                    self.settings_menu = translate_menu_keys(self.LEVEL_MENUS["seller"][2])
                    self.profile_menu = translate_menu_keys(self.LEVEL_MENUS[self.user_level][3])
                    self.store_menu = translate_menu_keys(self.LEVEL_MENUS[self.user_level][4])
                else:
                    # برگشت از حالت فروشنده
                    self.tel_menu = translate_menu_keys(self.LEVEL_MENUS[self.user_level][0])
                    self.extra_button_menu = translate_menu_keys(self.LEVEL_MENUS[self.user_level][1])
                    self.settings_menu = translate_menu_keys(self.LEVEL_MENUS[self.user_level][2])
                    self.profile_menu = translate_menu_keys(self.LEVEL_MENUS[self.user_level][3])
                    self.store_menu = translate_menu_keys(self.LEVEL_MENUS[self.user_level][4])

            # اگر زبان تغییر کرده باشه، فقط sync با user انجام بده (ترجمه تو send_menu)
            if old_instance.lang != self.lang and self.user:
                self.user.lang = self.lang
                self.user.save(update_fields=['lang'])

        super().save(*args, **kwargs)

   # ----------------------------
    # Address helper
    # ----------------------------
    def get_active_address(self):
        """آدرس فعال پروفایل را برمی‌گرداند"""
        return self.addresses.filter(shipping_is_active=True).first()
    
    def get_all_addresses(self):
        """همه آدرس‌های پروفایل را برمی‌گرداند"""
        return self.addresses.all()
    
    def set_active_address(self, address_id):
        """تنظیم آدرس فعال برای پروفایل"""
        try:
            # ابتدا همه آدرس‌ها را غیرفعال کن
            self.addresses.update(shipping_is_active=False)
            
            # آدرس مورد نظر را فعال کن
            address = self.addresses.get(id=address_id)
            address.shipping_is_active = True
            address.save()
            return True
        except Address.DoesNotExist:
            return False
        except Exception as e:
            # لاگ خطا
            print(f"Error setting active address: {e}")
            return False



class Address(models.Model):
    """
    مدل آدرس مشترک برای پروفایل‌ها و فروشگاه‌ها
    - هر پروفایل می‌تواند چندین آدرس داشته باشد (یک آدرس فعال)
    - هر فروشگاه فقط می‌تواند یک آدرس داشته باشد
    """
    profile = models.ForeignKey(
        "ProfileModel",  # استفاده از string reference برای جلوگیری از circular import
        on_delete=models.CASCADE, 
        related_name="addresses",
        null=True,      # برای آدرس‌های فروشگاه null است
        blank=True,     # برای آدرس‌های فروشگاه blank است
        verbose_name="Profile"
    )
    store = models.OneToOneField(
        "products.Store",  # استفاده از string reference
        on_delete=models.CASCADE,
        related_name="store_address",
        null=True,      # برای آدرس‌های پروفایل null است
        blank=True,     # برای آدرس‌های پروفایل blank است
        verbose_name="Store",
        unique=True     # مهم: این تضمین می‌کند هر فروشگاه فقط یک آدرس داشته باشد
    )
    
    # فیلدهای آدرس
    shipping_line1 = models.CharField(max_length=100, verbose_name="Address Line 1")
    shipping_line2 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Address Line 2")     
    shipping_country = models.CharField(max_length=50, verbose_name="Country")
    shipping_province = models.CharField(max_length=50, blank=True, null=True, verbose_name="Province")
    shipping_city = models.CharField(max_length=50, blank=True, null=True, verbose_name="City")
    shipping_zip_code = models.CharField(max_length=10, blank=True, null=True, verbose_name="Zip Code")
    shipping_home_phone = models.CharField(max_length=15, blank=True, null=True, verbose_name="Residential Phone Number")
    
    # فقط برای آدرس‌های پروفایل معنی دارد
    shipping_is_active = models.BooleanField(default=False, verbose_name="Active Address")



    class Meta:
        verbose_name = "Address"
        verbose_name_plural = "Addresses"
    
        constraints = [
            # یا profile یا store — نه هر دو
            models.CheckConstraint(
                condition=(
                    Q(profile__isnull=False, store__isnull=True) |
                    Q(profile__isnull=True, store__isnull=False)
                ),
                name="address_owner_check",
            ),
    
            # آدرس فعال فقط برای پروفایل‌ها
            models.CheckConstraint(
                condition=(
                    Q(profile__isnull=False) |
                    Q(shipping_is_active=False)
                ),
                name="active_address_only_for_profiles",
            ),
        ]
    
        indexes = [
            models.Index(fields=["profile", "shipping_is_active"]),
            models.Index(fields=["store"]),
        ] 


    def save(self, *args, **kwargs):
        """
        ذخیره آدرس با اعتبارسنجی و منطق business
        """
        # اعتبارسنجی قبل از ذخیره
        self._validate_ownership()
        
        # مدیریت آدرس فعال برای پروفایل‌ها
        if self.profile and self.shipping_is_active:
            # غیرفعال کردن سایر آدرس‌های فعال این پروفایل
            Address.objects.filter(
                profile=self.profile, 
                shipping_is_active=True
            ).exclude(pk=self.pk).update(shipping_is_active=False)
        
        super().save(*args, **kwargs)

    def _validate_ownership(self):
        """
        اعتبارسنجی مالکیت آدرس
        """
        from django.core.exceptions import ValidationError
        
        # آدرس باید یا متعلق به پروفایل باشد یا فروشگاه
        if not self.profile and not self.store:
            raise ValidationError("آدرس باید متعلق به یک پروفایل یا فروشگاه باشد.")
        
        # نمی‌تواند همزمان متعلق به هر دو باشد
        if self.profile and self.store:
            raise ValidationError("آدرس نمی‌تواند همزمان متعلق به پروفایل و فروشگاه باشد.")
        
        # shipping_is_active فقط برای آدرس‌های پروفایل معنی دارد
        if self.shipping_is_active and not self.profile:
            raise ValidationError("آدرس فعال فقط برای پروفایل‌ها قابل تعریف است.")

    def clean(self):
        """
        اعتبارسنجی منطقی برای فرم‌ها و admin
        """
        super().clean()
    
        # یا profile یا store — نه هر دو
        if self.profile and self.store:
            raise ValidationError(
                "آدرس نمی‌تواند همزمان متعلق به پروفایل و فروشگاه باشد."
            )
    
        # آدرس فعال فقط برای پروفایل
        if self.shipping_is_active and not self.profile:
            raise ValidationError(
                "آدرس فعال فقط برای پروفایل‌ها مجاز است."
            )
    
        # اگر متد جداگانه داری، اینجا صدا بزن
        if hasattr(self, "_validate_ownership"):
            self._validate_ownership() 

    def __str__(self):
        if self.profile:
            user_info = self.profile.user.username if hasattr(self.profile, 'user') and self.profile.user else self.profile.tel_id
            return f"Profile: {user_info} - {self.shipping_line1} ({'Active' if self.shipping_is_active else 'Inactive'})"
        elif self.store:
            return f"Store: {self.store.name} - {self.shipping_line1}"
        return f"Address: {self.shipping_line1}"

    @property
    def owner_type(self):
        """نوع مالک آدرس را برمی‌گرداند"""
        if self.profile:
            return "profile"
        elif self.store:
            return "store"
        return "unknown"

    @property
    def owner_name(self):
        """نام مالک آدرس را برمی‌گرداند"""
        if self.profile:
            if self.profile.user:
                return self.profile.user.username
            return self.profile.tel_id or f"Profile {self.profile.pk}"
        elif self.store:
            return self.store.name
        return "Unknown"

    @property 
    def shipping_country_name(self):
        """بررسی دیباگ"""
        print(f"DEBUG shipping_country_name called")
        print(f"  - Country code: {self.shipping_country}")
        print(f"  - Profile: {self.profile}")
        print(f"  - Store: {self.store}")
        
        if self.store:
            print(f"  - Store owner: {self.store.owner}")
            if self.store.owner:
                print(f"  - Store owner lang: {self.store.owner.lang}")
        
        if self.profile:
            print(f"  - Profile lang: {self.profile.lang}")
        
        result = self._get_translated_name('country', self.shipping_country)
        print(f"  - Result: {result}")
        return result

    @property
    def shipping_province_name(self):
        if not self.shipping_province:
            return None
        return self._get_translated_name('province', self.shipping_country, self.shipping_province)

    @property
    def shipping_city_name(self):
        if not self.shipping_city:
            return None
        return self._get_translated_name('city', self.shipping_country, self.shipping_province, self.shipping_city)

    def _get_translated_name(self, entity_type, country_code, province_name=None, city_name=None):
        # بارگذاری فایل JSON
        with open(settings.BASE_DIR / './utils/Data/countries_full_multilang.json', 'r', encoding='utf-8') as f:
            countries_data = json.load(f)

        # تشخیص زبان
        try:
            if self.store and self.store.owner:
                language = self.store.owner.lang  # ✅ اول از صاحب فروشگاه
                print(f"  - Language from store owner: {language}")
            elif self.profile:
                language = self.profile.lang  # ✅ سپس از پروفایل
                print(f"  - Language from profile: {language}")
            else:
                language = 'en'  # ✅ پیش‌فرض
                print(f"  - Default language: {language}")
        except Exception as e:
            print(f"  - Error getting language: {e}")
            language = 'en'

        # نگاشت زبان‌های ممکن به کدهای موجود در JSON
        language_map = {
            'fa': 'fa',  # فارسی
            'ar': 'ar',  # عربی
            'ru': 'ru',  # روسی
            'ch': 'ch',  # چینی
            'en': 'en',  # انگلیسی
        }

        lang_code = language_map.get(language, 'en')

        try:
            if entity_type == 'country':
                return countries_data[country_code]['names'].get(lang_code, countries_data[country_code]['names']['en'])

            elif entity_type == 'province':
                province_data = countries_data[country_code]['provinces'].get(province_name, {})
                if 'names' in province_data:
                    return province_data['names'].get(lang_code, province_data['names']['en'])
                return province_name  # اگر ترجمه وجود نداشت، نام انگلیسی را برگردان

            elif entity_type == 'city':
                province_data = countries_data[country_code]['provinces'].get(province_name, {})
                city_data = province_data.get('cities', {}).get(city_name, {})
                if 'names' in city_data:
                    return city_data['names'].get(lang_code, city_data['names']['en'])
                return city_name  # اگر ترجمه وجود نداشت، نام انگلیسی را برگردان

        except KeyError:
            # اگر داده‌ای یافت نشد، مقدار اصلی را برگردان
            if entity_type == 'country':
                return country_name
            elif entity_type == 'province':
                return province_name
            elif entity_type == 'city':
                return city_name

        return None


