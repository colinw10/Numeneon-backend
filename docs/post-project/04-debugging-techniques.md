# 🔍 Debugging Techniques

> Tools and strategies used to debug production issues

## The Problem

"It works on my machine" but not in production. How do you debug when you can't see the logs?

## Technique 1: Django Admin Panel

**URL:** `https://your-app.onrender.com/admin/`

The admin panel is your window into the production database.

### What to Check

| Section         | What It Tells You                               |
| --------------- | ----------------------------------------------- |
| **Messages**    | Are messages being saved? Who sent what?        |
| **Posts**       | Is `target_profile` being set on wall posts?    |
| **Users**       | Do the user IDs match what frontend is sending? |
| **Friendships** | Are friend relationships created properly?      |

### Quick Verification

If frontend says "I sent a message" but you don't see it in admin:

- ❌ **Backend isn't receiving the request**, OR
- ❌ **Backend is receiving but not saving**

## Technique 2: Debug Endpoints

Add temporary endpoints to inspect what's in the database:

```python
# backend/messages_app/views.py

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def debug_messages(request):
    """Debug endpoint to check all messages for current user."""
    user = request.user
    total_messages = Message.objects.count()
    user_messages = Message.objects.filter(
        Q(sender=user) | Q(receiver=user)
    ).count()

    sent = Message.objects.filter(sender=user).values(
        'receiver__username', 'content', 'created_at'
    )[:10]
    received = Message.objects.filter(receiver=user).values(
        'sender__username', 'content', 'created_at'
    )[:10]

    return Response({
        'total_messages_in_db': total_messages,
        'user_messages': user_messages,
        'user_id': user.id,
        'username': user.username,
        'recent_sent': list(sent),
        'recent_received': list(received),
    })
```

**Usage:** `GET /api/messages/debug/` with auth header

## Technique 3: Logging

Add logging to trace request flow:

```python
# backend/messages_app/views.py

import logging
logger = logging.getLogger(__name__)

class MessageListCreateView(generics.ListCreateAPIView):
    def create(self, request, *args, **kwargs):
        logger.info(f"Message create request from user {request.user.id}: {request.data}")
        response = super().create(request, *args, **kwargs)
        logger.info(f"Message created successfully: {response.data}")
        return response
```

**View logs on Render:** Dashboard → Logs tab

## Technique 4: Browser Network Tab

Before blaming backend, verify what frontend is sending:

1. Open DevTools → **Network** tab
2. Filter by `Fetch/XHR`
3. Perform the action (send message, create post)
4. Find the request
5. Check:
   - **Status Code:** 201 = saved, 400/500 = error
   - **Request Payload:** What did frontend send?
   - **Response:** What did backend return?

### Common Findings

| Status | Meaning            | Fix                  |
| ------ | ------------------ | -------------------- |
| 201    | Success            | Backend saved it     |
| 400    | Bad request        | Check payload format |
| 401    | Unauthorized       | Token expired?       |
| 404    | Not found          | Wrong URL            |
| 405    | Method not allowed | Wrong HTTP method    |
| 500    | Server error       | Check Render logs    |

## Technique 5: Test with Postman/cURL

Remove frontend from the equation:

```bash
# 1. Login to get token
curl -X POST https://numeneon-backend.onrender.com/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "pabloPistola", "password": "yourpassword"}'

# 2. Use token to create message
curl -X POST https://numeneon-backend.onrender.com/api/messages/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"receiver_id": 5, "content": "Test from curl"}'

# 3. Check if it saved
curl https://numeneon-backend.onrender.com/api/messages/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

If curl works but frontend doesn't → Frontend issue
If curl fails too → Backend issue

## Technique 6: Check the Database Directly

On Render, you can connect to PostgreSQL:

1. Go to your PostgreSQL service
2. Copy the "External Database URL"
3. Use `psql` or a GUI like TablePlus/pgAdmin

```sql
-- Check messages table
SELECT * FROM messages_app_message ORDER BY created_at DESC LIMIT 10;

-- Check if target_profile is being saved
SELECT id, author_id, target_profile_id, content
FROM posts_post
WHERE target_profile_id IS NOT NULL;
```

## Technique 7: Render Shell

Run Django commands directly on production:

1. Render Dashboard → Your Service → **Shell** tab
2. Run commands:

```bash
# Check messages
cd backend
python manage.py shell -c "
from messages_app.models import Message
print(f'Total messages: {Message.objects.count()}')
for m in Message.objects.all()[:5]:
    print(f'{m.sender.username} → {m.receiver.username}: {m.content[:30]}')"
```

## Debugging Checklist

When something doesn't work in production:

1. [ ] **Is it a frontend or backend issue?** Check Network tab
2. [ ] **Is the request reaching the server?** Check Render logs
3. [ ] **Is data being saved?** Check Django Admin
4. [ ] **Is the right data being saved?** Check field values in Admin
5. [ ] **Is data being returned correctly?** Check response in Network tab
6. [ ] **Does it work with direct API call?** Test with Postman/curl
7. [ ] **Is it a deployment issue?** Compare local vs production

## Common Production Issues

| Symptom                        | Likely Cause                             |
| ------------------------------ | ---------------------------------------- |
| Works locally, fails on Render | Environment variables, CORS, or database |
| Data disappears on refresh     | Not being saved (check serializer)       |
| WebSocket notifications fail   | InMemoryChannelLayer, need Redis         |
| 500 errors                     | Check Render logs for traceback          |
| "Not found" on API             | URL mismatch, trailing slash             |
| Auth fails                     | Token expired, CORS blocking             |

## Cleanup

Remember to remove debug endpoints before final deployment:

```python
# Don't leave this in production!
# path('debug/', views.debug_messages, name='debug-messages'),
```
