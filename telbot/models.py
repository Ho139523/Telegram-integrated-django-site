from django.db import models
from jinja2 import ModuleLoader
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
    

class CachedMedia(models.Model):
    MEDIA_TYPE_CHOICES = (
        ('video', 'video'),
        ('photo', 'photo'),
        ('document', 'document'),
    )

    profile = models.ForeignKey("accounts.ProfileModel", on_delete=models.CASCADE, related_name="Cachedmedia")
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPE_CHOICES, default='video')
    video_path = models.CharField(max_length=1024, unique=True)   # path on disk (برای مرجع)
    file_id = models.CharField(max_length=512, blank=True, null=True)  # telegram file_id
    channel_message_id = models.BigIntegerField(blank=True, null=True)
    channel_id = models.CharField(max_length=255, blank=True, null=True)  # e.g. @your_channel
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=True, null=False)
    
    def path(self, video_path):
        return video_path.split("/")[-1]
    
    @property
    def short_name(self):
        return f"{self.profile.lang}-{self.path(self.video_path)}"

    def __str__(self):
        return f"{self.media_type} - {self.path(self.video_path)}"

