# 🔧 Update: Messaging, Notifications & Wall Posts Fixes

> **Date:** January 30, 2026  
> **Author:** Pablo

---

## Summary

Fixed multiple issues affecting messaging, real-time notifications, and wall posts on the deployed app (Render + Vercel).

---

## Issues Fixed

### 1. WebSocket Notifications Not Working in Production

**Problem:** Real-time notifications (messages, friend requests) weren't reaching users in production.

**Cause:** `InMemoryChannelLayer` was being used, which only works for a single process. Render runs multiple workers, so notifications sent by one worker never reached users connected to another.

**Fix:** Updated `settings.py` to use Redis in production:

```python
# Before (broken in production)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# After (works with multiple workers)
import os
if os.environ.get('REDIS_URL'):
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                'hosts': [os.environ.get('REDIS_URL')],
            },
        },
    }
else:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }
```

**Action Required:** Set up Redis and add `REDIS_URL` environment variable in Render for real-time notifications to work.

---

### 2. Wall Posts Not Persisting

**Problem:** Posts made on another user's profile wall would appear temporarily but disappear after refresh.

**Cause:** The `target_profile` field existed in the database but wasn't being handled in the serializer.

**Fix:** Updated `posts/serializers.py` to accept and save `target_profile_id`:

```python
# Added to PostSerializer
target_profile_id = serializers.IntegerField(
    write_only=True,
    required=False,
    allow_null=True,
)

def create(self, validated_data):
    target_profile_id = validated_data.pop('target_profile_id', None)
    if target_profile_id:
        from django.contrib.auth.models import User
        validated_data['target_profile'] = User.objects.get(id=target_profile_id)
    return super().create(validated_data)
```

---

### 3. Frontend Fixes (Vercel)

These were fixed by the frontend team:

| Issue                             | Fix                                         |
| --------------------------------- | ------------------------------------------- |
| Messages not sending              | Changed `recieverId` → `receiver_id` (typo) |
| WebSocket using localhost in prod | Updated to use Render URL when deployed     |

---

## Files Changed

| File                                 | Change                                         |
| ------------------------------------ | ---------------------------------------------- |
| `backend/numeneon/settings.py`       | Use Redis for WebSocket channels in production |
| `backend/posts/models.py`            | Added `target_profile` field (already existed) |
| `backend/posts/serializers.py`       | Handle `target_profile_id` in create           |
| `backend/posts/views.py`             | Notify friends when a post is created          |
| `backend/notifications/utils.py`     | Added `notify_new_post` function               |
| `backend/notifications/consumers.py` | Added `new_post` WebSocket handler             |
| `.gitignore`                         | Added `venv_new/`                              |

---

### 4. Post Notifications to Friends

**Problem:** When a user creates a post, their friends aren't notified in real-time.

**Fix:** Added notification logic to `perform_create` in posts views:

```python
# backend/posts/views.py
from friends.models import Friendship
from notifications.utils import notify_new_post

def perform_create(self, serializer):
    post = serializer.save(author=self.request.user)

    # Notify all friends about the new post
    friendships = Friendship.objects.filter(user=self.request.user)
    post_data = PostSerializer(post).data

    for friendship in friendships:
        notify_new_post(friendship.friend.id, post_data)
```

Added `notify_new_post` to `notifications/utils.py` and `new_post` handler to `notifications/consumers.py`.

**Frontend Action:** Handle `new_post` notification type in WebSocket listener to update feed in real-time.

---

## Environment Variables Needed (Render)

| Key         | Description                                      |
| ----------- | ------------------------------------------------ |
| `REDIS_URL` | Redis connection URL for WebSocket notifications |

**Options for Redis:**

- Render Redis (~$7/month)
- Upstash Redis (free tier available)

---

## Testing Checklist

After deployment:

- [ ] Can search for users in chat
- [ ] Can send messages to users
- [ ] Messages persist after refresh
- [ ] Wall posts appear on target user's profile
- [ ] Wall posts persist after refresh
- [ ] (With Redis) Real-time message notifications work
- [ ] (With Redis) Friend request notifications work
- [ ] (With Redis) Friends receive post notifications in real-time

---

## Related Docs

- [WebSocket Deployment Guide](../../websockets/06-render-deployment.md)
- [CORS Configuration](../../deployment/cors-configuration.md)
