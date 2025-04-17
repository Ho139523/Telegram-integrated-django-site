from django.db import models
from accounts.models import User
from accounts.models import ProfileModel


    
        
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
