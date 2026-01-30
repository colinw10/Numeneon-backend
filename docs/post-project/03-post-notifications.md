# 🔔 Post Notifications to Friends

> **Feature:** When a user creates a post, notify all their friends in real-time

## The Goal

When Pablo posts something:
1. All Pablo's friends receive a WebSocket notification
2. Their feed can update in real-time (optional frontend implementation)
3. Works even if friend is on a different Render worker (requires Redis)

## Implementation

### 1. Add Notification Utility

```python
# backend/notifications/utils.py

def notify_new_post(to_user_id, post_data):
    """
    Send a new post notification to a friend.

    Args:
        to_user_id: ID of user to notify (a friend)
        post_data: Serialized post data
    """
    notify_user(to_user_id, 'new_post', post_data)
```

### 2. Add WebSocket Consumer Handler

```python
# backend/notifications/consumers.py

class NotificationConsumer(AsyncWebsocketConsumer):
    # ... existing handlers ...

    async def new_post(self, event):
        """Handler for new post notifications (from friends)."""
        await self.send(text_data=json.dumps({
            'type': 'new_post',
            'data': event['data']
        }))
```

### 3. Update Post View to Notify Friends

```python
# backend/posts/views.py

from friends.models import Friendship
from notifications.utils import notify_new_post

class PostViewSet(viewsets.ModelViewSet):
    # ... existing code ...

    def perform_create(self, serializer):
        # Save the post
        post = serializer.save(author=self.request.user)
        
        # Get all friends (Friendship model is directional)
        friendships = Friendship.objects.filter(user=self.request.user)
        
        # Serialize post data for notification
        post_data = PostSerializer(post).data
        
        # Notify each friend
        for friendship in friendships:
            notify_new_post(friendship.friend.id, post_data)
```

## Understanding the Friendship Model

The Friendship model is **directional**:

```python
# backend/friends/models.py

class Friendship(models.Model):
    user = models.ForeignKey(User, related_name='friendships')
    friend = models.ForeignKey(User, related_name='friends')
    created_at = models.DateTimeField(auto_now_add=True)
```

When two users become friends, **two records are created**:
```
| id | user_id | friend_id |
|----|---------|-----------|
| 1  |    5    |     8     |  ← Pablo → Tito
| 2  |    8    |     5     |  ← Tito → Pablo
```

So `Friendship.objects.filter(user=request.user)` returns all friends of the current user.

## WebSocket Message Format

When a friend posts, connected clients receive:

```json
{
  "type": "new_post",
  "data": {
    "id": 456,
    "author": {
      "id": 5,
      "username": "pabloPistola"
    },
    "content": "Just posted something!",
    "type": "thoughts",
    "created_at": "2026-01-30T15:30:00Z",
    "target_profile": null,
    "likes_count": 0,
    "reply_count": 0
  }
}
```

## Frontend Integration

The frontend needs to handle the `new_post` type in the WebSocket listener:

```javascript
// Example WebSocket handler
websocket.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch(message.type) {
    case 'new_message':
      // Handle new DM
      break;
    case 'friend_request':
      // Handle friend request
      break;
    case 'friend_accepted':
      // Handle friend accepted
      break;
    case 'new_post':
      // Handle new post from friend
      // Option 1: Show notification toast
      showToast(`${message.data.author.username} posted something!`);
      // Option 2: Add to feed if on feed page
      if (onFeedPage) {
        setPosts(prev => [message.data, ...prev]);
      }
      break;
  }
};
```

## Requirements

- **Redis** must be set up for production (see [01-websocket-production-fix.md](01-websocket-production-fix.md))
- Without Redis, notifications only work in local development

## Testing

1. Open app in two browsers
2. Log in as friends (User A and User B)
3. As User A, create a post
4. User B should receive a WebSocket message with type `new_post`
5. Check browser DevTools → Network → WS tab to see the message

## Files Changed

| File | Change |
|------|--------|
| `backend/notifications/utils.py` | Added `notify_new_post` function |
| `backend/notifications/consumers.py` | Added `new_post` handler |
| `backend/posts/views.py` | Updated `perform_create` to notify friends |

## Future Improvements

1. **Batch notifications** - If user posts rapidly, don't spam friends
2. **Notification preferences** - Let users mute post notifications
3. **Only notify for certain post types** - Maybe not milestones?
4. **Activity feed** - Store notifications in DB for users who are offline
