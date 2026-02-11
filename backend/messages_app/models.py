# 📩 MESSAGES - Direct messaging between users
"""
Message model - user-to-user private messaging
"""

from django.db import models
from django.contrib.auth.models import User


class Message(models.Model):
    """
    Message model for direct messaging between users.
    Each message has a sender, receiver, content, and read status.
    
    Optional: Can include a reply_to_story reference for story replies.
    """
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_messages'
    )
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Optional: Link message to a story (for "Replied to your story" feature)
    reply_to_story = models.ForeignKey(
        'stories.Story',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='replies'
    )

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username} → {self.receiver.username}: {self.content[:30]}..."
