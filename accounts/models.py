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
from functools import lru_cache
from django.core.exceptions import ValidationError


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
        return ["menu_wallet", "menu_buy_by_code", "menu_categories", "menu_support", "menu_create_shop", "menu_settings"]

    def default_extra_button_menu():
        return ["menu_cart"]

    def default_settings_menu():
        return ["menu_become_seller", "menu_my_address", "menu_profile", "menu_store"]

    def default_profile_menu():
        return ["menu_language", "currency_settings"]
    
    def default_store_menu():
        return ["menu_language", "currency_settings"]

    def get_default_store():
        from products.models import Store  # import inside function to avoid circular import
        try:
            return Store.objects.get(name="Intelleum").pk
        except Store.DoesNotExist:
            return None  # fallback, so migrations won't break
    
    @staticmethod
    def get_currency_choices():
        currencies = []

        for currency in pycountry.currencies:
            if currency.alpha_3 == "IRR":
                # جایگزین IRR با IRT
                currencies.append(
                    (
                        "IRT",
                        f"IRT - Iranian Toman"
                    )
                )
            currencies.append(
                (
                    currency.alpha_3,
                    f"{currency.alpha_3} - {currency.name}"
                )
            )

        return sorted(currencies, key=lambda x: x[1])

    def get_currency(self):
        """
        بر اساس کشور کاربر، واحد پولی مناسب را برمی‌گرداند.
        """
        country_currency_map = {
            'IR': 'IRT',  # Iran
            'US': 'USD',  # United States
            'GB': 'GBP',  # United Kingdom
            'EU': 'EUR',  # European Union
            'RU': 'RUB',  # Russia
            'CN': 'CNY',  # China
            'AE': 'AED',  # United Arab Emirates
            'IN': 'INR',  # India
            'JP': 'JPY',  # Japan
            'CA': 'CAD',  # Canada
            'AU': 'AUD',  # Australia
            'BR': 'BRL',  # Brazil
            'ZA': 'ZAR',  # South Africa
            'MX': 'MXN',  # Mexico
            'KR': 'KRW',  # South Korea
            'SA': 'SAR',  # Saudi Arabia
            'TR': 'TRY',  # Turkey
            'EG': 'EGP',  # Egypt
            'NG': 'NGN',  # Nigeria
            'PK': 'PKR',  # Pakistan
            'IQ': 'IQD',  # Iraq
            'OM': 'OMR', # Omman
            'QA': 'QAR', # Qatar
            'AF': 'AFN', # Afghanistan
            'KW': 'KWD', # Kuwait
            'BH': 'BHD', # Bahrain
            'LB': 'LBP', # Lebanon
            'SY': 'SYP', # Syria
            'YE': 'YER', # Yemen
            'TM': 'TMT', # Turkmenistan
            'ARM': 'AMD', # Armenia
            'AZ': 'AZN', # Azerbaijan
            'GE': 'GEL', # Georgia
            'KZ': 'KZT', # Kazakhstan
            'UZ': 'UZS', # Uzbekistan
            'KG': 'KGS', # Kyrgyzstan
            'TJ': 'TJS', # Tajikistan
            'MN': 'MNT', # Mongolia
            'BD': 'BDT', # Bangladesh
            'LK': 'LKR', # Sri Lanka
            'TH': 'THB', # Thailand
            'VN': 'VND', # Vietnam
            'MY': 'MYR', # Malaysia
            'SG': 'SGD', # Singapore
            'NZ': 'NZD', # New Zealand
            'PH': 'PHP', # Philippines
            'ID': 'IDR', # Indonesia
            'KH': 'KHR', # Cambodia
        }

        if self.lang:
            lang_country_map = {
                'fa': 'IR',
                'en': 'US',
                'ar': 'AE',
                'ru': 'RU',
                'zh': 'CN',
                'es': 'ES',
                'fr': 'FR',
                'de': 'DE',
                'it': 'IT',
                'pt': 'PT',
                'ja': 'JP',
                'ko': 'KR',
                'tr': 'TR',
                'eg': 'EG',
                'ng': 'NG',
                'pk': 'PK',
                'iq': 'IQ',
                'om': 'OM',
                'qa': 'QA',
                'af': 'AF',
                'kw': 'KW',
                'bh': 'BH',
                'lb': 'LB',
                'sy': 'SY',
                'ye': 'YE',
                'tm': 'TM',
                'am': 'AM',
                'az': 'AZ',
                'ge': 'GE',
                'kz': 'KZ',
                'uz': 'UZ',
                'kg': 'KG',
                'tj': 'TJ',
                'mn': 'MN',
                'bd': 'BD',
                'lk': 'LK',
                'th': 'TH',
                'vn': 'VN',
                'my': 'MY',
                'sg': 'SG',
                'nz': 'NZ',
                'ph': 'PH',
                'id': 'ID',
                'kh': 'KH',
            }
            country_code = lang_country_map.get(self.lang, None)
            if country_code:
                return country_currency_map.get(country_code, 'USD')

        return 'USD'

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
    hidden_videos = models.JSONField(default=dict, blank=True, null=False, verbose_name="Hidden Videos")
    currency = models.CharField(max_length=3, choices=get_currency_choices(), default='IRT', verbose_name='Currency')

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
            ["menu_wallet", "menu_buy_by_code", "menu_categories", "menu_support", "menu_create_shop", "menu_settings"],
            ["menu_cart"],
            ["menu_become_seller", "menu_my_address", "menu_profile"],
            ["menu_language"],
            ["menu_language"],
        ],
        'green': [
            ["menu_wallet", "menu_buy_by_code", "menu_categories", "menu_support", "menu_create_shop", "menu_settings"],
            ["menu_cart"],
            ["menu_become_seller", "menu_my_address", "menu_profile"],
            ["menu_language"],
            ["menu_language"],
        ],
        'silver': [
            ["menu_wallet", "menu_quick_buy", "menu_support"],
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

    - هر پروفایل می‌تواند چندین آدرس داشته باشد ولی فقط یکی فعال باشد.
    - هر فروشگاه فقط یک آدرس دارد.
    """

    profile = models.ForeignKey(
        "ProfileModel",
        on_delete=models.CASCADE,
        related_name="addresses",
        null=True,
        blank=True,
        verbose_name="Profile",
    )

    store = models.OneToOneField(
        "products.Store",
        on_delete=models.CASCADE,
        related_name="store_address",
        null=True,
        blank=True,
        verbose_name="Store",
    )

    shipping_line1 = models.CharField(max_length=100)
    shipping_line2 = models.CharField(max_length=100, blank=True, null=True)

    shipping_country = models.CharField(max_length=50)
    shipping_province = models.CharField(max_length=50, blank=True, null=True)
    shipping_city = models.CharField(max_length=50, blank=True, null=True)

    shipping_zip_code = models.CharField(max_length=10, blank=True, null=True)
    shipping_home_phone = models.CharField(max_length=15, blank=True, null=True)

    # فقط برای پروفایل معنا دارد
    shipping_is_active = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Address"
        verbose_name_plural = "Addresses"

        constraints = [

            # دقیقا یکی از profile یا store باید مقدار داشته باشد
            models.CheckConstraint(
                condition=(
                    Q(profile__isnull=False, store__isnull=True)
                    |
                    Q(profile__isnull=True, store__isnull=False)
                ),
                name="address_owner_check",
            ),

            # آدرس فعال فقط برای پروفایل
            models.CheckConstraint(
                condition=(
                    Q(profile__isnull=False)
                    |
                    Q(shipping_is_active=False)
                ),
                name="active_address_only_for_profiles",
            ),
        ]

        indexes = [
            models.Index(fields=["profile", "shipping_is_active"]),
            models.Index(fields=["store"]),
        ]

    def clean(self):

        super().clean()

        if bool(self.profile) == bool(self.store):
            raise ValidationError(
                "آدرس باید فقط متعلق به پروفایل یا فقط متعلق به فروشگاه باشد."
            )

        if self.shipping_is_active and not self.profile:
            raise ValidationError(
                "آدرس فعال فقط برای پروفایل‌ها مجاز است."
            )

    def save(self, *args, **kwargs):

        self.full_clean()

        super().save(*args, **kwargs)

        # اگر این آدرس فعال باشد، سایر آدرس‌های پروفایل غیرفعال شوند
        if self.profile and self.shipping_is_active:
            Address.objects.filter(
                profile=self.profile,
                shipping_is_active=True,
            ).exclude(
                pk=self.pk
            ).update(
                shipping_is_active=False
            )

    def __str__(self):

        if self.profile:
            if self.profile.user:
                owner = self.profile.user.username
            else:
                owner = self.profile.tel_id

            return (
                f"Profile: {owner} - "
                f"{self.shipping_line1} "
                f"({'Active' if self.shipping_is_active else 'Inactive'})"
            )

        if self.store:
            return f"Store: {self.store.name} - {self.shipping_line1}"

        return self.shipping_line1

    @property
    def owner_type(self):

        if self.profile:
            return "profile"

        if self.store:
            return "store"

        return "unknown"

    @property
    def owner_name(self):

        if self.profile:

            if self.profile.user:
                return self.profile.user.username

            return self.profile.tel_id or f"Profile {self.profile.pk}"

        if self.store:
            return self.store.name

        return "Unknown"

    @property
    def shipping_country_name(self):

        return self._get_translated_name(
            "country",
            self.shipping_country,
        )

    @property
    def shipping_province_name(self):

        if not self.shipping_province:
            return None

        return self._get_translated_name(
            "province",
            self.shipping_country,
            self.shipping_province,
        )

    @property
    def shipping_city_name(self):

        if not self.shipping_city:
            return None

        return self._get_translated_name(
            "city",
            self.shipping_country,
            self.shipping_province,
            self.shipping_city,
        )

    @staticmethod
    @lru_cache(maxsize=1)
    def _countries_data():

        with open(
            settings.BASE_DIR / "utils/Data/countries_full_multilang.json",
            "r",
            encoding="utf-8",
        ) as f:

            return json.load(f)

    def _get_language(self):

        if self.store and self.store.owner:
            return self.store.owner.lang or "en"

        if self.profile:
            return self.profile.lang or "en"

        return "en"

    def _get_translated_name(
        self,
        entity_type,
        country_code,
        province_name=None,
        city_name=None,
    ):

        countries_data = self._countries_data()

        language_map = {
            "fa": "fa",
            "ar": "ar",
            "ru": "ru",
            "ch": "ch",
            "en": "en",
        }

        lang = language_map.get(
            self._get_language(),
            "en",
        )

        try:

            country = countries_data[country_code]

            if entity_type == "country":

                return country["names"].get(
                    lang,
                    country["names"]["en"],
                )

            if entity_type == "province":

                province = country["provinces"].get(
                    province_name,
                    {},
                )

                return province.get(
                    "names",
                    {},
                ).get(
                    lang,
                    province_name,
                )

            if entity_type == "city":

                province = country["provinces"].get(
                    province_name,
                    {},
                )

                city = province.get(
                    "cities",
                    {},
                ).get(
                    city_name,
                    {},
                )

                return city.get(
                    "names",
                    {},
                ).get(
                    lang,
                    city_name,
                )

        except Exception:
            pass

        if entity_type == "country":
            return country_code

        if entity_type == "province":
            return province_name

        return city_name


