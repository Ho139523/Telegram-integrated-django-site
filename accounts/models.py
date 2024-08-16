from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    special_user=models.DateTimeField(default=timezone.now)
    
    def is_special_user(self):
        if special_user > timezone.now():
            return True
        else:
            return False
