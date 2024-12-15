from django.db import models
from accounts.models import User
from accounts.models import ProfileModel

class telbotid(models.Model):
    profile = models.OneToOneField(ProfileModel, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    tel_id = models.CharField(max_length=100, null=False, blank=False)
    credit = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True)
    
    def __str__(self):
        return f"Telbot ID: {self.telegram_id} - Credit: {self.credit}"
    