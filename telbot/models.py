from django.db import models
from accounts.models import User
from accounts.models import ProfileModel
from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import ProfileModel
#from .models import telbotid

class telbotid(models.Model):
    profile = models.OneToOneField(ProfileModel, unique=True, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, unique=True, on_delete=models.SET_NULL, null=True, blank=True)
    tel_id = models.CharField(max_length=100, unique=True, null=False, blank=False)
    credit = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True)
    
    def __str__(self):
        return f"Telbot ID: {self.tel_id} - Credit: {self.credit}"
        
        
class ConversationModel(models.Model):
    user_id = models.BigIntegerField()
    username = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    started_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation with {self.user_id}"


class MessageModel(models.Model):
    conversation = models.ForeignKey(ConversationModel, on_delete=models.CASCADE, related_name="messages")
    sender_id = models.BigIntegerField()
    text = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    message_id = models.BigIntegerField(null=True, blank=True)

    def __str__(self):
        return f"Message from {self.sender_id} at {self.sent_at}"



@receiver(post_save, sender=telbotid)
def sync_profile_credit_from_telbot(sender, instance, **kwargs):
    if hasattr(instance, '_syncing'):
        return
    instance._syncing = True
    profile = instance.profile
    if profile and profile.credit != instance.credit:
        profile.credit = instance.credit
        profile._syncing = True
        profile.save()
    del instance._syncing