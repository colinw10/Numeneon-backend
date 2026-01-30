# 🔌 WebSocket Production Fix

> **Problem:** Real-time notifications not working on Render

## The Issue

When deployed to Render, WebSocket notifications (messages, friend requests) weren't reaching users.

### Symptoms
- Could send messages via REST API
- Messages saved to database
- But recipients never received real-time notifications
- No WebSocket errors in console

## Root Cause

Django Channels was using `InMemoryChannelLayer`:

```python
# ❌ This only works for single-process apps
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}
```

**Why this fails on Render:**
- Render runs multiple workers (processes) for your app
- `InMemoryChannelLayer` stores messages in RAM of one process
- If User A connects to Worker 1 and User B to Worker 2...
- Worker 1 can't send messages to Worker 2's memory
- Notifications are lost!

```
Worker 1 (RAM)          Worker 2 (RAM)
┌─────────────┐         ┌─────────────┐
│ User A      │    ✗    │ User B      │
│ connected   │─────────│ connected   │
│             │ Can't   │             │
│ sends msg   │ reach!  │ waiting...  │
└─────────────┘         └─────────────┘
```

## The Solution

Use Redis as a shared message broker between workers:

```python
# ✅ Works with multiple workers
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
    # Local development can still use InMemory
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }
```

**How Redis fixes it:**

```
Worker 1                   Redis                    Worker 2
┌─────────────┐       ┌─────────────┐         ┌─────────────┐
│ User A      │       │             │         │ User B      │
│ connected   │──────▶│  Message    │────────▶│ connected   │
│             │       │  Queue      │         │             │
│ sends msg   │       │             │         │ receives!   │
└─────────────┘       └─────────────┘         └─────────────┘
```

## Files Changed

**backend/numeneon/settings.py:**
- Added conditional CHANNEL_LAYERS configuration

## Dependencies

Already in `requirements.txt`:
```
channels==4.0.0
channels_redis==4.2.0
daphne==4.1.0
```

## Environment Variables

| Key | Value | Where |
|-----|-------|-------|
| `REDIS_URL` | `redis://...` or `rediss://...` | Render Dashboard → Environment |

## Redis Options

| Provider | Cost | Notes |
|----------|------|-------|
| **Upstash** | Free tier (10K commands/day) | Recommended for small projects |
| **Render Redis** | ~$7/month | Easier setup, same platform |
| **Redis Cloud** | Free tier available | More features |

## How to Set Up Upstash (Free)

1. Go to [upstash.com](https://upstash.com)
2. Create account → Create Database
3. Select region closest to Render (e.g., us-east-1)
4. Copy the `REDIS_URL` (use the one with TLS/SSL)
5. Add to Render: Dashboard → Environment → Add `REDIS_URL`
6. Redeploy

## Testing

After setting up Redis:

1. Open app in two different browsers/incognito
2. Log in as different users
3. Send a friend request
4. Other user should see notification immediately
5. Send a message
6. Recipient should see it in real-time

## Key Learnings

1. **Always use a message broker in production** - InMemoryChannelLayer is only for development
2. **Check worker count** - If your app runs >1 process, you need Redis
3. **WebSocket errors are silent** - The connection works, but messages get lost
4. **Redis is cheap/free** - No reason not to use it
