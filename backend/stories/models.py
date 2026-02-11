"""
Stories Feature Models

Instagram-style stories that expire after 24 hours.
Users can upload images/videos, view friends' stories, and react with heart or thunder.
"""
import uuid
from datetime import timedelta

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Story(models.Model):
    """
    A story post that expires after 24 hours.
    Media is uploaded to Cloudinary on frontend before creating the story.
    """
    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories')
    media_url = models.URLField(max_length=500)  # Cloudinary URL
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    caption = models.TextField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # Set to created_at + 24 hours on save

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Stories'

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.user.username}'s story - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class StoryView(models.Model):
    """
    Tracks which users have viewed a story.
    Used to show view counts and mark stories as seen.
    """
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='views')
    viewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='viewed_stories')
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['story', 'viewer']

    def __str__(self):
        return f"{self.viewer.username} viewed {self.story.user.username}'s story"


class StoryReaction(models.Model):
    """
    Reactions to stories - heart or thunder.
    One reaction per user per story (can update reaction type).
    """
    REACTION_CHOICES = [
        ('heart', 'Heart'),
        ('thunder', 'Thunder'),
    ]

    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='story_reactions')
    reaction_type = models.CharField(max_length=10, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['story', 'user']  # One reaction per user per story

    def __str__(self):
        return f"{self.user.username} reacted {self.reaction_type} to {self.story.user.username}'s story"
