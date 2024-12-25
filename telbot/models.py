from django.db import models
from accounts.models import User
from accounts.models import ProfileModel

class telbotid(models.Model):
    profile = models.OneToOneField(ProfileModel, unique=True, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, unique=True, on_delete=models.SET_NULL, null=True, blank=True)
    tel_id = models.CharField(max_length=100, unique=True, null=False, blank=False)
    credit = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True)
    
    def __str__(self):
        return f"Telbot ID: {self.tel_id} - Credit: {self.credit}"
        
        
class Conversation(models.Model):
    user_id = models.BigIntegerField()
    username = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    started_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation with {self.user_id}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender_id = models.BigIntegerField()
    text = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    message_id = models.BigIntegerField(null=True, blank=True)

    def __str__(self):
        return f"Message from {self.sender_id} at {self.sent_at}"
    