from rest_framework import serializers
from .models import Post, Like
from users.serializers import UserSerializer
from django.contrib.auth.models import User


class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    target_profile = UserSerializer(read_only=True)
    mentioned_user = UserSerializer(read_only=True)

    reply_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    parent_id = serializers.PrimaryKeyRelatedField(
        queryset=Post.objects.all(),
        source="parent",
        write_only=True,
        required=False,
        allow_null=True,
    )

    # Wall posts: ID of user whose wall this post should appear on
    target_profile_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='target_profile',
        write_only=True,
        required=False,
        allow_null=True,
    )

    # Reply to specific comment (for threaded replies)
    reply_to_comment_id = serializers.PrimaryKeyRelatedField(
        queryset=Post.objects.all(),
        source='reply_to_comment',
        write_only=True,
        required=False,
        allow_null=True,
    )

    # Mentioned user in a reply (for @mentions)
    mentioned_user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='mentioned_user',
        write_only=True,
        required=False,
        allow_null=True,
    )

    # Write-only field for mentioned username (for display in notifications)
    mentioned_username = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = Post
        fields = [
            "id",
            "author",
            "content",
            "type",
            "media_url",
            "created_at",
            "updated_at",
            "parent",
            "parent_id",
            "target_profile",
            "target_profile_id",
            "reply_to_comment",
            "reply_to_comment_id",
            "mentioned_user",
            "mentioned_user_id",
            "mentioned_username",
            "reply_count",
            "likes_count",
            "comment_count",
            "shares_count",
            "is_liked",
        ]
        read_only_fields = [
            "author",
            "created_at",
            "updated_at",
            "parent",
            "target_profile",
            "reply_to_comment",
            "mentioned_user",
            "reply_count",
            "is_liked",
        ]

    def create(self, validated_data):
        # Remove mentioned_username from validated_data as it's not a model field
        validated_data.pop('mentioned_username', None)
        return super().create(validated_data)

    def get_reply_count(self, obj):
        return obj.replies.count()

    def get_is_liked(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Like.objects.filter(user=request.user, post=obj).exists()
        return False


