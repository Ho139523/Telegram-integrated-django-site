from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone



provinces=(
('West Azerbaija', 'West Azerbaija',),
('East Azerbaijan', 'East Azerbaijan',),
('Ardabil', 'Ardabil',),
('Kurdistan', 'Kurdistan',),
('Zanjan', 'Zanjan',),
('Gilan', 'Gilan',),
('Kermanshah', 'Kermanshah',),
('Hamadan', 'Hamadan',),
('Qazvin', 'Qazvin',),
('Ilam', 'Ilam',),
('Lorestan', 'Lorestan',),
('Markazi', 'Markazi',),
('Qom', 'Qom',),
('Tehran', 'Tehran',),
('Alborz', 'Alborz',),
('Mazandaran', 'Mazandaran',),
('Golestan', 'Golestan',),
('North Khorasan', 'North Khorasan',),
('Khuzestan', 'Khuzestan',),
('Chaharmahal and Bakhtiari', 'Chaharmahal and Bakhtiari',),
('Kohgiluyeh and Boyer-Ahmad', 'Kohgiluyeh and Boyer-Ahmad',),
('Isfahan', 'Isfahan',),
('Semnan', 'Semnan',),
('Razavi Khorasan', 'Razavi Khorasan',),
('Yazd', 'Yazd',),
('South Khorasan', 'South Khorasan',),
('Bushehr', 'Bushehr',),
('Fars', 'Fars',),
('Kerman', 'Kerman',),
('Sistan and Baluchestan', 'Sistan and Baluchestan',),
('Hormozgan', 'Hormozgan'))
        
class IranAddressModel(models.Model):
    line1=models.CharField(max_length=300, verbose_name="Address Line 1")
    line2=models.CharField(max_length=300, verbose_name="Address Line 2")
    city=models.CharField(max_length=10, verbose_name="City")
    province=models.CharField(max_length=30, choices=provinces, verbose_name="Province")
    zip=models.CharField(max_length=10, verbose_name="Zip Code")
    phone=models.CharField(max_length=8, verbose_name="Residential Phone Number")
    
    def __str__(self):
        return "Zipcode: " + self.zip + ", " + self.city + ", " + self.province




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
    fname=models.CharField(max_length=100, blank=True, null=True)
    lname=models.CharField(max_length=150, blank=True, null=True)
    avatar=models.ImageField(default="registration/user_avatars/default-avatar.png", upload_to="registration/user_avatars")
    background_pic=models.ImageField(default="registration/user_headers/default_header.avif", upload_to="registration/user_headers")
    birthday=models.DateField(blank=True, null=True)
    Phone=models.CharField(max_length=10, blank=True, null=True)
    address=models.ForeignKey(IranAddressModel, blank=True, null=True, on_delete=models.SET_NULL)
    about_me=models.TextField(max_length=1000, blank=True, null=True, default="Describe yourself, your capabilities and talents here. Let others know how awesome you are ;)")
    instagram=models.CharField(max_length=120, blank=True, null=True)
    tweeter=models.CharField(max_length=120, blank=True, null=True)
    
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

        
        
        
    
    