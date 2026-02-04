# Reply-to-Comment Feature with @Mentions

> **Last Updated:** February 4, 2026  
> **Status:** ✅ Implemented

---

## Overview

This feature enables users to reply directly to comments with @mentions. When a user replies to a comment, the mentioned user receives a real-time WebSocket notification.

---

## Backend Changes

### 1. Post Model Updates

**File:** `backend/posts/models.py`

Two new fields were added to the `Post` model:

```python
# Reply to specific comment (for threaded replies)
reply_to_comment = models.ForeignKey(
    "self",
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="comment_replies",
)

# Mentioned user in a reply (for @mentions)
mentioned_user = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="mentions",
)
```

### 2. Serializer Updates

**File:** `backend/posts/serializers.py`

New fields added to `PostSerializer`:

| Field                 | Type                                | Description                                             |
| --------------------- | ----------------------------------- | ------------------------------------------------------- |
| `reply_to_comment_id` | PrimaryKeyRelatedField (write-only) | ID of the comment being replied to                      |
| `mentioned_user_id`   | PrimaryKeyRelatedField (write-only) | ID of the user being mentioned                          |
| `mentioned_username`  | CharField (write-only)              | Username being mentioned (for display in notifications) |
| `mentioned_user`      | UserSerializer (read-only)          | Full user object of mentioned user                      |

### 3. View Updates

**File:** `backend/posts/views.py`

The `perform_create` method now checks for comment replies with @mentions and sends appropriate notifications:

```python
# If this is a reply to a specific comment with @mention
if post.reply_to_comment and post.mentioned_user and post.mentioned_user != self.request.user:
    notify_comment_reply(
        post.mentioned_user.id,
        self.request.user,
        post_data,
        post.parent.id if post.parent else None,
        mentioned_username
    )
```

### 4. Notification Utility

**File:** `backend/notifications/utils.py`

New function added:

```python
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
```

### 5. WebSocket Consumer Handler

**File:** `backend/notifications/consumers.py`

New handler added:

```python
async def comment_reply(self, event):
    """Handler for comment reply notifications (someone replied to your comment with @mention)."""
    await self.send(text_data=json.dumps({
        'type': 'comment_reply',
        'data': event['data']
    }))
```

---

## API Usage

### Creating a Comment Reply with @Mention

**Endpoint:** `POST /api/posts/`

**Request Body:**

```json
{
  "content": "@username your reply message here...",
  "parent_id": 123,
  "mentioned_user_id": 456,
  "mentioned_username": "username",
  "reply_to_comment_id": 789
}
```

**Fields Explained:**

| Field                 | Required | Description                                  |
| --------------------- | -------- | -------------------------------------------- |
| `content`             | Yes      | The reply text (should start with @username) |
| `parent_id`           | Yes      | ID of the original post being commented on   |
| `mentioned_user_id`   | No       | ID of the user being @mentioned              |
| `mentioned_username`  | No       | Username being @mentioned                    |
| `reply_to_comment_id` | No       | ID of the specific comment being replied to  |

**Response (201 Created):**

```json
{
  "id": 790,
  "author": {
    "id": 1,
    "username": "replier",
    "first_name": "John",
    "last_name": "Doe"
  },
  "content": "@username your reply message here...",
  "type": "thoughts",
  "parent": 123,
  "reply_to_comment": 789,
  "mentioned_user": {
    "id": 456,
    "username": "username"
  },
  "created_at": "2026-02-04T12:00:00Z"
}
```

---

## WebSocket Notification

When a comment reply with @mention is created, the mentioned user receives a WebSocket notification:

**Event Type:** `comment_reply`

**Payload:**

```json
{
  "type": "comment_reply",
  "data": {
    "message": "replier replied to your comment",
    "replier": {
      "id": 1,
      "username": "replier",
      "first_name": "John",
      "last_name": "Doe"
    },
    "reply": {
      "content": "@username your reply message here...",
      "id": 790
    },
    "post": {
      "id": 123
    },
    "mentioned_username": "username"
  }
}
```

---

## Database Migration

After deploying these changes, run migrations:

```bash
python manage.py makemigrations posts
python manage.py migrate
```

---

## Frontend Integration

The frontend expects:

1. **ThreadView Component** - Reply button on each comment that opens an inline reply input
2. **@mention highlighting** - Styled with cyan color and clickable
3. **NotificationContext** - Listener for `comment_reply` WebSocket events
4. **NotificationModal** - Displays "replied to your comment" notifications

See frontend documentation for implementation details.

---

## Notification Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      Comment Reply Flow                         │
└─────────────────────────────────────────────────────────────────┘

User A clicks "Reply" on User B's comment
            │
            ▼
┌─────────────────────────────────────────┐
│ Frontend sends POST /api/posts/         │
│ {                                       │
│   content: "@userB reply text",         │
│   parent_id: <post_id>,                 │
│   mentioned_user_id: <userB_id>,        │
│   mentioned_username: "userB",          │
│   reply_to_comment_id: <comment_id>     │
│ }                                       │
└─────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────┐
│ Backend creates Post record             │
│ Backend calls notify_comment_reply()    │
└─────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────┐
│ WebSocket sends to user_<userB_id>      │
│ { type: "comment_reply", data: {...} }  │
└─────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────┐
│ User B's frontend receives notification │
│ NotificationModal displays alert        │
└─────────────────────────────────────────┘
```
