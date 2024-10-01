from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone




        
class ShippingAddressModel(models.Model):
    profile=models.OneToOneField("ProfileModel", on_delete=models.CASCADE, verbose_name="User Profile")
    shipping_line1=models.CharField(max_length=40, blank=True, null=True, verbose_name="Address Line 1")
    shipping_line2=models.CharField(max_length=40, blank=True, null=True, verbose_name="Address Line 2")
    shipping_country=models.CharField(max_length=10, blank=True, null=True, verbose_name="Country")
    shipping_city=models.CharField(max_length=10, blank=True, null=True, verbose_name="City")
    shipping_province=models.CharField(max_length=30, blank=True, null=True, verbose_name="Province")
    shipping_zip=models.CharField(max_length=10, blank=True, null=True, verbose_name="Zip Code")
    shipping_home_phone=models.CharField(max_length=8, blank=True, null=True, verbose_name="Residential Phone Number")
    
    def __str__(self):
        return "Zipcode: " + str(self.shipping_zip) + ", " + str(self.shipping_city) + ", " + str(self.shipping_province)




class User(AbstractUser):
    special_user=models.DateTimeField(default=timezone.now)
    
    def is_special_user(self):
        if self.special_user > timezone.now():
            return True
        else:
            return False
    
    is_special_user.boolean=True
    is_special_user.short_description="Special User"
    
    
    
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
    instagram=models.CharField(max_length=120, blank=True, null=True, verbose_name="Instagram ID")
    tweeter=models.CharField(max_length=120, blank=True, null=True, verbose_name="Tweeter ID")
    
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

        
        
        
    
    