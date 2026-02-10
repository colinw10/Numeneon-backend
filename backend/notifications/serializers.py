"""
Serializers for the notifications app.
Handles push subscription data validation.
"""
from rest_framework import serializers
from .models import PushSubscription


class PushSubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for browser push subscriptions.
    
    Expected input format from frontend:
    {
        "endpoint": "https://fcm.googleapis.com/...",
        "keys": {
            "p256dh": "BNcRd...",
            "auth": "tB..."
        }
    }
    """
    # Accept nested keys object from frontend
    keys = serializers.DictField(write_only=True, required=True)
    
    class Meta:
        model = PushSubscription
        fields = ['id', 'endpoint', 'keys', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def validate_keys(self, value):
        """Ensure keys contains p256dh and auth."""
        if 'p256dh' not in value:
            raise serializers.ValidationError("keys must contain 'p256dh'")
        if 'auth' not in value:
            raise serializers.ValidationError("keys must contain 'auth'")
        return value
    
    def create(self, validated_data):
        """
        Create subscription, extracting keys from nested object.
        If subscription with this endpoint exists, update it instead.
        """
        keys = validated_data.pop('keys')
        user = self.context['request'].user
        
        # Update or create (same endpoint = same browser/device)
        subscription, created = PushSubscription.objects.update_or_create(
            endpoint=validated_data['endpoint'],
            defaults={
                'user': user,
                'p256dh': keys['p256dh'],
                'auth': keys['auth'],
            }
        )
        return subscription
