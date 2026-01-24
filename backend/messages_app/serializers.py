from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Message


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for message display"""
    class Meta:
        model = User
        fields = ['id', 'username']


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for Message model"""
    sender = UserBasicSerializer(read_only=True)
    receiver = UserBasicSerializer(read_only=True)
    receiver_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Message
        fields = ['id', 'sender', 'receiver', 'receiver_id', 'content', 'is_read', 'created_at']
        read_only_fields = ['id', 'sender', 'created_at']

    def create(self, validated_data):
        receiver_id = validated_data.pop('receiver_id')
        receiver = User.objects.get(id=receiver_id)
        validated_data['receiver'] = receiver
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)


class ConversationSerializer(serializers.Serializer):
    """Serializer for conversation list (grouped by user)"""
    user = UserBasicSerializer()
    last_message = MessageSerializer()
    unread_count = serializers.IntegerField()
