from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import pycountry
from django.core.validators import MinLengthValidator, int_list_validator
from django.utils.translation import gettext_lazy as _
import json
from django.utils.translation import get_language
from django.conf import settings

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

    def get_language_choices():
        languages = []
        for lang in pycountry.languages:
            if hasattr(lang, 'alpha_2'):  # فقط زبان‌های با کد دو حرفی
                languages.append((lang.alpha_2, lang.name))
        return sorted(languages, key=lambda x: x[1])

    def default_tel_menu():
        return [
            "🧮 موجودی", "خرید با کد کالا", "🗂 دسته بندی ها",
            "🖥 بازدید سایت", "💬 پیام به پشتیبان", "تنظیمات ⚙"
        ]
    def default_extra_button_menu():
        return ["🔐     ایجاد حساب کاربری    🛡️",]

    def default_settings_menu():
        return ["فروشنده شو", "پروفایل"]

    def default_profile_menu():
        return ['زبان 🌐']

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
    Phone = models.CharField(max_length=10, blank=True, null=True, verbose_name="Phone Number")
    about_me = models.TextField(
        max_length=1000,
        blank=True,
        null=True,
        default="Describe yourself, your capabilities and talents here. Let others know how awesome you are ;)",
        verbose_name="About Me"
    )
    instagram = models.CharField(max_length=120, unique=True, blank=True, null=True, verbose_name="Instagram ID")
    tweeter = models.CharField(max_length=120, unique=True, blank=True, null=True, verbose_name="Tweeter ID")
    telegram = models.CharField(max_length=120, unique=True, blank=True, null=True, verbose_name="Telegram ID")
    credit = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=False, blank=True)
    tel_id = models.CharField(
        max_length=10,
        validators=[int_list_validator(sep=''), MinLengthValidator(10)],
        default='100000000',
        unique=True,
        null=False,
        blank=True
    )
    tel_menu = models.JSONField(default=default_tel_menu, blank=True, null=False)
    extra_button_menu = models.JSONField(default=default_extra_button_menu, blank=True, null=False)
    seller_mode = models.BooleanField(default=False, blank=False, null=False)
    settings_menu = models.JSONField(default=default_settings_menu, blank=True, null=False)
    profile_menu = models.JSONField(default=default_profile_menu, blank=True, null=False)
    lang = models.CharField(max_length=10, choices=get_language_choices(), default='fa', unique=False, null=False, blank=True)

    def get_active_address(self):
        """برگرداندن آدرس فعال کاربر"""
        return self.addresses.filter(is_active=True).first()

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
            [
                "🧮 موجودی", "خرید با کد کالا", "🗂 دسته بندی ها",
                "🖥 بازدید سایت","💬 پیام به پشتیبان", "تنظیمات ⚙"
            ],
            ["🔐     ایجاد حساب کاربری    🛡️",],
            ["فروشنده شو", "آدرس پستی من", "پروفایل 👤"],
            ['زبان 🌐'],
        ],
        'green': [
            [
                "🧮 موجودی", "خرید با کد کالا", "🗂 دسته بندی ها",
                "🖥 بازدید سایت","💬 پیام به پشتیبان", "تنظیمات ⚙"
            ],
            [""],
            ["فروشنده شو", "آدرس پستی من", "پروفایل 👤"],
            ['زبان 🌐'],
        ],
        'silver': [
            [
                "🧮 موجودی", "🛒 خرید سریع", "🖥 بازدید سایت", "💬 پیام به پشتیبان"
            ],
            [""],
            ["فروشنده شو", "آدرس پستی من", "پروفایل 👤"],
            ['زبان 🌐'],
        ],
        'gold': [
            [
                "💰 گزارش مالی", "🛒 خرید پیشرفته", "📊 تحلیل‌ها", "🖥 بازدید سایت"
            ],
            [""],
            ["فروشنده شو", "آدرس پستی من", "پروفایل 👤"],
            ['زبان 🌐'],
        ],
        'seller': [
            [
                "افزودن کالا", "حذف کالا", "آدرس پستی من", "💰 گزارش مالی", "📊 تحلیل‌ها", "تنظیمات ⚙"
            ],
            ["آمار فروش"],
            ["بازگشت به حالت خریدار", "تغییر آدرس انبار", "پروفایل 👤"],
            ['زبان 🌐'],
        ],
    }

    def __str__(self):
        if self.user:
            return self.user.username
        elif self.tel_id:
            return self.tel_id

    @property
    def age(self):
        if self.birthday:
            today = timezone.now().date()
            age = (
                    today.year - self.birthday.year
                    - ((today.month, today.day) < (self.birthday.month, self.birthday.day))
            )
            return age
        return None

    def save(self, *args, **kwargs):
        if self.pk:
            old_instance = ProfileModel.objects.get(pk=self.pk)

            # Sync language to user if it changed
            if old_instance.lang != self.lang and self.user:
                self.user.lang = self.lang
                self.user.save(update_fields=['lang'])

            # تغییر منوها بر اساس سطح کاربری یا فروشنده بودن
            if old_instance.user_level != self.user_level and self.user_level in self.LEVEL_MENUS:
                self.tel_menu = self.LEVEL_MENUS[self.user_level][0]
                self.extra_button_menu = self.LEVEL_MENUS[self.user_level][1]
                self.settings_menu = self.LEVEL_MENUS[self.user_level][2]
                self.profile_menu = self.LEVEL_MENUS[self.user_level][3]

            if old_instance.seller_mode:
                self.tel_menu = self.LEVEL_MENUS["seller"][0]
                self.extra_button_menu = self.LEVEL_MENUS["seller"][1]
                self.settings_menu = self.LEVEL_MENUS["seller"][2]
                self.profile_menu = self.LEVEL_MENUS[self.user_level][3]

            if not old_instance.seller_mode:
                self.tel_menu = self.LEVEL_MENUS[self.user_level][0]
                self.extra_button_menu = self.LEVEL_MENUS[self.user_level][1]
                self.settings_menu = self.LEVEL_MENUS[self.user_level][2]
                self.profile_menu = self.LEVEL_MENUS[self.user_level][3]

        # Sync language from user if it wasn't manually changed
        elif self.user and self.lang != self.user.lang:
            self.lang = self.user.lang

        super().save(*args, **kwargs)



class Address(models.Model):
    profile = models.ForeignKey(ProfileModel, on_delete=models.CASCADE, related_name="addresses")
    shipping_line1 = models.CharField(max_length=100, verbose_name="Address Line 1")
    shipping_line2 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Address Line 2")

    # فقط CharField بدون choices
    shipping_country = models.CharField(max_length=50, verbose_name="Country")
    shipping_province = models.CharField(max_length=50, blank=True, null=True, verbose_name="Province")
    shipping_city = models.CharField(max_length=50, blank=True, null=True, verbose_name="City")

    shipping_zip_code = models.CharField(max_length=10, blank=True, null=True, verbose_name="Zip Code")
    shipping_home_phone = models.CharField(max_length=15, blank=True, null=True, verbose_name="Residential Phone Number")

    shipping_is_active = models.BooleanField(default=False, verbose_name="Active Address")

    def save(self, *args, **kwargs):
        if self.shipping_is_active:
            Address.objects.filter(profile=self.profile, shipping_is_active=True).update(shipping_is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        user_info = self.profile.user.username if hasattr(self.profile, 'user') and self.profile.user else self.profile.tel_id
        return f"{user_info} - {self.shipping_line1} ({'Active' if self.shipping_is_active else 'Inactive'})"




    @property
    def shipping_country_name(self):
        return self._get_translated_name('country', self.shipping_country)

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

        # تشخیص زبان کاربر
        try:
            language = self.profile.lang # فرض می‌کنیم فیلد language در ProfileModel وجود دارد
        except:
            language = 'en'  # زبان پیش‌فرض

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
                return country_code
            elif entity_type == 'province':
                return province_name
            elif entity_type == 'city':
                return city_name

        return None
