from django.db import models
from accounts.models import User

class telbotid(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    tel_id = models.CharField(max_length=100, null=False, blank=False)
    
    def __str__(self):
        return self.user or self.tel_id
    