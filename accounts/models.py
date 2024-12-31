from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from utils.variables.countries import countries
from django.db.models.signals import post_save
from django.dispatch import receiver
#from .models import ProfileModel  # مدل پروفایل
from telbot.models import telbotid  # مدل مرتبط از اپ ربات تلگرام



        
class ShippingAddressModel(models.Model):
    profile=models.OneToOneField("ProfileModel", on_delete=models.CASCADE, verbose_name="User Profile")
    shipping_line1=models.CharField(max_length=40, blank=True, null=True, verbose_name="Address Line 1")
    shipping_line2=models.CharField(max_length=40, blank=True, null=True, verbose_name="Address Line 2")
    shipping_country=models.CharField(max_length=10, choices=countries, blank=True, null=True, verbose_name="Country")
    shipping_city=models.CharField(max_length=10, blank=True, null=True, verbose_name="City")
    shipping_province=models.CharField(max_length=30, blank=True, null=True, verbose_name="Province")
    shipping_zip=models.CharField(max_length=10, blank=True, null=True, verbose_name="Zip Code")
    shipping_home_phone=models.CharField(max_length=8, blank=True, null=True, verbose_name="Residential Phone Number")
    
    def __str__(self):
        return "profile: "+ str(self.profile) + ", " +"Zipcode: " + str(self.shipping_zip) + ", " + str(self.shipping_city) + ", " + str(self.shipping_province) + ", " + str(self.shipping_country)




class User(AbstractUser):
    special_user = models.DateTimeField(default=timezone.now)

    def is_special_user(self):
        return self.special_user > timezone.now()
    
    is_special_user.boolean = True
    is_special_user.short_description = "Special User"
    
    def save(self, *args, **kwargs):
        # Lowercase and trim the username before saving
        self.username = self.username.strip().lower()
        super().save(*args, **kwargs)

    # Make username queries case-insensitive
    def get_by_natural_key(self, username):
        return self.__class__.objects.get(username__iexact=username.strip())


    
    
class ProfileModel(models.Model):
    
    user=models.OneToOneField(User, unique=True, on_delete=models.CASCADE)
    fname=models.CharField(max_length=100, blank=True, null=True, verbose_name="First Name")
    lname=models.CharField(max_length=150, blank=True, null=True, verbose_name="Last Name")
    avatar=models.ImageField(default="registration/user_avatars/default-avatar.png", upload_to="registration/user_avatars")
    background_pic=models.ImageField(default="registration/user_headers/default_header.avif", upload_to="registration/user_headers", verbose_name="Header Image")
    birthday=models.DateField(blank=True, null=True)
    Phone=models.CharField(max_length=10, blank=True, null=True, verbose_name="Phone Number")
    address=models.OneToOneField(ShippingAddressModel, blank=True, null=True, on_delete=models.SET_NULL)
    about_me=models.TextField(max_length=1000, blank=True, null=True, default="Describe yourself, your capabilities and talents here. Let others know how awesome you are ;)", verbose_name="About Me")
    instagram=models.CharField(max_length=120, unique=True, blank=True, null=True, verbose_name="Instagram ID")
    tweeter=models.CharField(max_length=120, unique=True, blank=True, null=True, verbose_name="Tweeter ID")
    telegram=models.CharField(max_length=120, unique=True, blank=True, null=True, verbose_name="Telegram ID")
    credit=models.DecimalField(max_digits=10, decimal_places=2, default=0, null=False, blank=True)
    
    def __str__(self):
        return self.user.username


    @property
    def age(self):
        today = timezone.now().date()
        age = int(
            today.year
            - (self.birthday.year)
            - ((today.month, today.day) < (self.birthday.month, self.birthday.day))
        )
        return age


@receiver(post_save, sender=ProfileModel)
def sync_telbot_credit_from_profile(sender, instance, **kwargs):
    if hasattr(instance, '_syncing'):
        return  # جلوگیری از حلقه بی‌نهایت
    instance._syncing = True
    telbot, created = telbotid.objects.get_or_create(profile=instance)
    if telbot.credit != instance.credit:
        telbot.credit = instance.credit
        telbot._syncing = True
        telbot.save()
    del instance._syncing