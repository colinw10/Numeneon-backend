"""
Utility functions to send WebSocket notifications.

Usage in views:
    from notifications.utils import notify_friend_request

    notify_friend_request(user_id=5, from_user=request.user, request_id=123)
"""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import logging

logger = logging.getLogger(__name__)


def notify_user(user_id, notification_type, data):
    """
    Send a notification to a specific user via WebSocket.

    Args:
        user_id: The ID of the user to notify
        notification_type: Type of notification (e.g., 'friend_request', 'new_message')
        data: Dictionary containing notification data
    """
    try:
        channel_layer = get_channel_layer()
        logger.info(f"notify_user called: user_id={user_id}, type={notification_type}, channel_layer={type(channel_layer)}")
        
        if channel_layer is None:
            logger.warning("Channel layer is None, skipping notification")
            return
            
        group_name = f'user_{user_id}'
        logger.info(f"Sending to group: {group_name}")

        # Send message to the user's group
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': notification_type.replace('-', '_'),
                'data': data
            }
        )
        logger.info(f"Notification sent successfully to {group_name}")
    except Exception as e:
        logger.error(f"Failed to send notification: {e}", exc_info=True)
        # Don't re-raise - notifications should not break the main request


def notify_friend_request(to_user_id, from_user, request_id):
    """
    Send a friend request notification.

    Args:
        to_user_id: ID of user receiving the request
        from_user: User object who sent the request
        request_id: ID of the FriendRequest object
    """
    notify_user(to_user_id, 'friend_request', {
        'request_id': request_id,
        'from_user': {
            'id': from_user.id,
            'username': from_user.username,
            'first_name': from_user.first_name,
            'last_name': from_user.last_name,
        }
    })


def notify_friend_accepted(to_user_id, friend):
    """
    Send a friend accepted notification.

    Args:
        to_user_id: ID of user who originally sent the request
        friend: User object who accepted the request
    """
    notify_user(to_user_id, 'friend_accepted', {
        'friend': {
            'id': friend.id,
            'username': friend.username,
            'first_name': friend.first_name,
            'last_name': friend.last_name,
        }
    })


def notify_new_message(to_user_id, message_data):
    """
    Send a new message notification.

    Args:
        to_user_id: ID of user receiving the message
        message_data: Serialized message data
    """
    notify_user(to_user_id, 'new_message', message_data)


def notify_new_post(to_user_id, post_data):
    """
    Send a new post notification to a friend.

    Args:
        to_user_id: ID of user to notify (a friend)
        post_data: Serialized post data
    """
    notify_user(to_user_id, 'new_post', post_data)


def notify_post_comment(to_user_id, commenter, post_data, comment_data):
    """
    Send a notification when someone comments on a post.

    Args:
        to_user_id: ID of the post author to notify
        commenter: User object who made the comment
        post_data: Serialized original post data
        comment_data: Serialized comment/reply data
    """
    notify_user(to_user_id, 'post_comment', {
        'message': f'{commenter.username} commented on your post',
        'commenter': {
            'id': commenter.id,
            'username': commenter.username,
            'first_name': commenter.first_name,
            'last_name': commenter.last_name,
        },
        'post': post_data,
        'comment': comment_data,
    })


def notify_comment_reply(to_user_id, replier, reply_data, post_id, mentioned_username):
    """
    Send a notification when someone replies to a comment with @mention.

    Args:
        to_user_id: ID of the mentioned user to notify
        replier: User object who made the reply
        reply_data: Serialized reply data
        post_id: ID of the original post
        mentioned_username: Username that was mentioned
    """
    notify_user(to_user_id, 'comment_reply', {
        'message': f'{replier.username} replied to your comment',
        'replier': {
            'id': replier.id,
            'username': replier.username,
            'first_name': replier.first_name,
            'last_name': replier.last_name,
        },
        'reply': {
            'content': reply_data.get('content', ''),
            'id': reply_data.get('id'),
        },
        'post': {
            'id': post_id,
        },
        'mentioned_username': mentioned_username,
    })


# =============================================================================
# PUSH NOTIFICATIONS (for when app is closed)
# =============================================================================

def send_push_notification(user_id, title, body, data=None, icon=None, badge=None, tag=None):
    """
    Send a push notification to all of a user's subscribed devices/browsers.
    
    This works even when the app is completely closed, as the browser's
    service worker handles receiving the push.
    
    Args:
        user_id: The ID of the user to send push to
        title: Notification title (required)
        body: Notification body text (required)
        data: Optional dict of custom data to include (e.g., {'url': '/messages/123'})
        icon: Optional URL to notification icon
        badge: Optional URL to badge icon (for mobile)
        tag: Optional tag to group/replace notifications
    
    Returns:
        dict with 'success' count and 'failed' count
    """
    import json
    from django.conf import settings
    
    # Import here to make the dependency optional
    try:
        from pywebpush import webpush, WebPushException
    except ImportError:
        logger.error("pywebpush not installed. Run: pip install pywebpush")
        return {'success': 0, 'failed': 0, 'error': 'pywebpush not installed'}
    
    # Import PushSubscription model
    from .models import PushSubscription
    
    # Check VAPID configuration
    vapid_private_key = getattr(settings, 'VAPID_PRIVATE_KEY', '')
    vapid_claims = getattr(settings, 'VAPID_CLAIMS', {})
    
    if not vapid_private_key:
        logger.warning("VAPID_PRIVATE_KEY not configured, skipping push notification")
        return {'success': 0, 'failed': 0, 'error': 'VAPID not configured'}
    
    # Get all push subscriptions for this user
    subscriptions = PushSubscription.objects.filter(user_id=user_id)
    
    if not subscriptions.exists():
        logger.info(f"No push subscriptions found for user {user_id}")
        return {'success': 0, 'failed': 0, 'error': 'No subscriptions'}
    
    # Build the notification payload
    payload = {
        'title': title,
        'body': body,
        'data': data or {},
    }
    if icon:
        payload['icon'] = icon
    if badge:
        payload['badge'] = badge
    if tag:
        payload['tag'] = tag
    
    payload_json = json.dumps(payload)
    
    success_count = 0
    failed_count = 0
    expired_endpoints = []
    
    for subscription in subscriptions:
        try:
            webpush(
                subscription_info=subscription.to_subscription_info(),
                data=payload_json,
                vapid_private_key=vapid_private_key,
                vapid_claims=vapid_claims
            )
            success_count += 1
            logger.info(f"Push sent successfully to user {user_id}")
        except WebPushException as e:
            logger.error(f"Push failed for user {user_id}: {e}")
            failed_count += 1
            
            # If subscription expired (410 Gone), mark for deletion
            if e.response and e.response.status_code == 410:
                expired_endpoints.append(subscription.endpoint)
        except Exception as e:
            logger.error(f"Unexpected error sending push to user {user_id}: {e}")
            failed_count += 1
    
    # Clean up expired subscriptions
    if expired_endpoints:
        PushSubscription.objects.filter(endpoint__in=expired_endpoints).delete()
        logger.info(f"Deleted {len(expired_endpoints)} expired push subscriptions")
    
    return {'success': success_count, 'failed': failed_count}


def push_friend_request(to_user_id, from_user):
    """
    Send push notification for a friend request.
    """
    send_push_notification(
        user_id=to_user_id,
        title='New Friend Request',
        body=f'{from_user.username} wants to be your friend!',
        data={
            'type': 'friend_request',
            'url': '/friends',
            'from_user_id': from_user.id
        },
        tag='friend-request'
    )


def push_friend_accepted(to_user_id, friend):
    """
    Send push notification when friend request is accepted.
    """
    send_push_notification(
        user_id=to_user_id,
        title='Friend Request Accepted',
        body=f'{friend.username} accepted your friend request!',
        data={
            'type': 'friend_accepted',
            'url': f'/profile/{friend.id}',
            'friend_id': friend.id
        },
        tag='friend-accepted'
    )


def push_new_message(to_user_id, from_user, message_preview):
    """
    Send push notification for a new message.
    
    Args:
        to_user_id: User receiving the message
        from_user: User who sent the message
        message_preview: First ~50 chars of the message
    """
    send_push_notification(
        user_id=to_user_id,
        title=f'Message from {from_user.username}',
        body=message_preview[:100] + ('...' if len(message_preview) > 100 else ''),
        data={
            'type': 'new_message',
            'url': f'/messages/{from_user.id}',
            'from_user_id': from_user.id
        },
        tag=f'message-{from_user.id}'  # Group messages from same user
    )


def push_post_comment(to_user_id, commenter, post_id):
    """
    Send push notification when someone comments on your post.
    """
    send_push_notification(
        user_id=to_user_id,
        title='New Comment',
        body=f'{commenter.username} commented on your post',
        data={
            'type': 'post_comment',
            'url': f'/posts/{post_id}',
            'post_id': post_id,
            'commenter_id': commenter.id
        },
        tag=f'comment-{post_id}'
    )


def push_comment_reply(to_user_id, replier, post_id):
    """
    Send push notification when someone replies to your comment.
    """
    send_push_notification(
        user_id=to_user_id,
        title='New Reply',
        body=f'{replier.username} replied to your comment',
        data={
            'type': 'comment_reply',
            'url': f'/posts/{post_id}',
            'post_id': post_id,
            'replier_id': replier.id
        },
        tag=f'reply-{post_id}'
    )