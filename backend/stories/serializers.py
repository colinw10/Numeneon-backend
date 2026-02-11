"""
Stories Feature Serializers

Handles serialization of Story, StoryView, and StoryReaction models.
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Story, StoryView, StoryReaction


class StoryUserSerializer(serializers.ModelSerializer):
    """
    Minimal user data for story display.
    Includes profile picture from the Profile model.
    """
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'profile_picture']

    def get_profile_picture(self, obj):
        """Get avatar from user's profile if it exists."""
        if hasattr(obj, 'profile') and obj.profile.avatar:
            return obj.profile.avatar
        return None


class StorySerializer(serializers.ModelSerializer):
    """
    Full story serializer with user info, view status, and reactions.
    """
    user = StoryUserSerializer(read_only=True)
    is_viewed = serializers.SerializerMethodField()
    my_reaction = serializers.SerializerMethodField()
    view_count = serializers.SerializerMethodField()
    heart_count = serializers.SerializerMethodField()
    thunder_count = serializers.SerializerMethodField()

    class Meta:
        model = Story
        fields = [
            'id', 'user', 'media_url', 'media_type', 'caption',
            'created_at', 'expires_at', 'is_viewed', 'my_reaction',
            'view_count', 'heart_count', 'thunder_count'
        ]
        read_only_fields = ['id', 'created_at', 'expires_at']

    def get_is_viewed(self, obj):
        """Check if current user has viewed this story."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.views.filter(viewer=request.user).exists()
        return False

    def get_my_reaction(self, obj):
        """Get current user's reaction type (heart/thunder) or null."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            reaction = obj.reactions.filter(user=request.user).first()
            return reaction.reaction_type if reaction else None
        return None

    def get_view_count(self, obj):
        """Total number of views on this story."""
        return obj.views.count()

    def get_heart_count(self, obj):
        """Count of heart reactions."""
        return obj.reactions.filter(reaction_type='heart').count()

    def get_thunder_count(self, obj):
        """Count of thunder reactions."""
        return obj.reactions.filter(reaction_type='thunder').count()


class StoryCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new stories.
    Only accepts media_url, media_type, and optional caption.
    """
    class Meta:
        model = Story
        fields = ['media_url', 'media_type', 'caption']

    def validate_media_type(self, value):
        """Ensure media_type is valid."""
        if value not in ['image', 'video']:
            raise serializers.ValidationError("media_type must be 'image' or 'video'")
        return value

    def create(self, validated_data):
        """Create story with the authenticated user."""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class StoryReactionSerializer(serializers.ModelSerializer):
    """
    Serializer for story reactions.
    """
    class Meta:
        model = StoryReaction
        fields = ['reaction_type']

    def validate_reaction_type(self, value):
        """Ensure reaction_type is valid."""
        if value not in ['heart', 'thunder']:
            raise serializers.ValidationError("reaction_type must be 'heart' or 'thunder'")
        return value
