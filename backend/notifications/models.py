from django.db import models
from django.contrib.auth.models import User


class PushSubscription(models.Model):
    """
    Stores browser push notification subscriptions for users.
    
    When a user enables push notifications on their browser/PWA,
    we store their subscription info here to send them notifications
    even when the app is closed.
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='push_subscriptions'
    )
    # The push service endpoint URL (unique per browser/device)
    endpoint = models.URLField(max_length=500, unique=True)
    # p256dh key for encryption
    p256dh = models.CharField(max_length=100)
    # auth secret for encryption
    auth = models.CharField(max_length=50)
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Push Subscription'
        verbose_name_plural = 'Push Subscriptions'
    
    def __str__(self):
        return f"{self.user.username}'s push subscription"
    
    def to_subscription_info(self):
        """
        Returns the subscription in the format pywebpush expects.
        """
        return {
            "endpoint": self.endpoint,
            "keys": {
                "p256dh": self.p256dh,
                "auth": self.auth
            }
        }
