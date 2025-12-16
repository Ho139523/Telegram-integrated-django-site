from rest_framework import serializers
from .models import ConversationModel, MessageModel, CachedMedia

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageModel
        fields = '__all__'

class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = ConversationModel
        fields = ['id', 'user_id', 'username', 'is_active', 'started_at', 'messages']

class CachedMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CachedMedia
        fields = '__all__'
