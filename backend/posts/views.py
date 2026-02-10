# 🟢 COLIN - Posts Backend Lead
# views.py - API endpoints for posts (using ViewSet approach)

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
import logging

from .models import Post, Like
from .serializers import PostSerializer
from friends.models import Friendship
from notifications.utils import notify_new_post, notify_post_comment, notify_comment_reply

logger = logging.getLogger(__name__)


class PostViewSet(viewsets.ModelViewSet):
 
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        logger.info(f"Post create request: {request.data}")
        try:
            response = super().create(request, *args, **kwargs)
            logger.info(f"Post created successfully: {response.data}")
            return response
        except Exception as e:
            logger.error(f"Post creation failed: {e}", exc_info=True)
            raise

    def get_queryset(self):
        qs = Post.objects.all()

        if self.action == "list":
            qs = qs.filter(parent__isnull=True)

            username = self.request.query_params.get("username")
            if username:
                # Profile page: show user's own posts AND posts on their wall
                from django.db.models import Q
                qs = qs.filter(
                    Q(author__username=username, target_profile__isnull=True) |  # Their own posts (not wall posts)
                    Q(target_profile__username=username)  # Posts on their wall
                )
            else:
                # Main feed: exclude wall posts (only show regular posts)
                qs = qs.filter(target_profile__isnull=True)

        return qs

    def perform_create(self, serializer):
        # Get mentioned_username from request data before saving
        mentioned_username = self.request.data.get('mentioned_username', '')
        
        post = serializer.save(author=self.request.user)
        
        # Increment comment_count on parent post if this is a reply/comment
        if post.parent:
            post.parent.comment_count += 1
            post.parent.save(update_fields=['comment_count'])
        
        try:
            post_data = PostSerializer(post, context={'request': self.request}).data
            
            # If this is a reply to a specific comment with @mention, send comment_reply notification
            if post.reply_to_comment and post.mentioned_user and post.mentioned_user != self.request.user:
                notify_comment_reply(
                    post.mentioned_user.id,
                    self.request.user,
                    post_data,
                    post.parent.id if post.parent else None,
                    mentioned_username or post.mentioned_user.username
                )
            # If this is a reply/comment, notify the original post author
            elif post.parent and post.parent.author != self.request.user:
                parent_data = PostSerializer(post.parent, context={'request': self.request}).data
                notify_post_comment(
                    post.parent.author.id,
                    self.request.user,
                    parent_data,
                    post_data
                )
            # If this is a wall post, notify the wall owner
            elif post.target_profile and post.target_profile != self.request.user:
                from notifications.utils import notify_user
                notify_user(
                    post.target_profile.id,
                    'wall_post',
                    {
                        'message': f'{self.request.user.username} posted on your wall',
                        'post': post_data,
                        'author': {
                            'id': self.request.user.id,
                            'username': self.request.user.username
                        }
                    }
                )
            elif not post.parent:
                # Regular post (not a reply): notify all friends
                friendships = Friendship.objects.filter(user=self.request.user)
                for friendship in friendships:
                    notify_new_post(friendship.friend.id, post_data)
        except Exception as e:
            # Don't fail the post creation if notifications fail
            logger.error(f"Failed to send post notifications: {e}")

    @action(detail=True, methods=["get"])
    def replies(self, request, pk=None):
        post = self.get_object()
        replies = Post.objects.filter(parent=post)
        serializer = self.get_serializer(replies, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def like(self, request, pk=None):
        post = self.get_object()
        user = request.user

        existing = Like.objects.filter(user=user, post=post).first()
        if existing:
            existing.delete()
            post.likes_count = max(0, post.likes_count - 1)
        else:
            Like.objects.create(user=user, post=post)
            post.likes_count += 1

        post.save()
        serializer = self.get_serializer(post)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def share(self, request, pk=None):
        post = self.get_object()
        post.shares_count += 1
        post.save()

        serializer = self.get_serializer(post)
        return Response(serializer.data, status=status.HTTP_200_OK)

