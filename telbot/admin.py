from django.contrib import admin
from .models import (
    CachedMedia
)

@admin.register(CachedMedia)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('short_name', 'channel_message_id', 'channel_id', 'created_at')
    list_filter = ('channel_id', 'created_at')
    search_fields = ('video_path', "short_name")
    ordering = ['created_at']

