# Backend Setup & Updates

> **Last Updated:** February 10, 2026

---

## 🚀 Pull Latest Changes

```bash
git pull origin dev
```

---

## 📦 Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**New packages added:**

- `gunicorn` - Production WSGI server
- `dj-database-url` - Database URL parsing
- `python-dotenv` - Environment variable loading
- `pywebpush` - Web Push notifications (VAPID)

---

## 🗄️ Database

Using **PostgreSQL** via `DATABASE_URL` environment variable.

If you don't have it set, add to your `.env`:

```
DATABASE_URL=postgresql://user:password@host:port/dbname
```

Run migrations:

```bash
python manage.py migrate
```

---

## � Messages App (NEW)

The `messages_app` provides direct messaging between users.

### Setup After Pulling

```bash
cd backend
python manage.py migrate          # Creates messages_app tables
python manage.py seed_messages    # Seeds sample conversations
```

**Required users for seeding:** `pabloPistola`, `arthurb`, `nataliap`, `colinw`, `crystalr`, `titod`

### Messages API Endpoints

All endpoints require authentication (`Authorization: Bearer <token>`)

| Method | Endpoint                                     | Description                     |
| ------ | -------------------------------------------- | ------------------------------- |
| GET    | `/api/messages/`                             | List all your messages          |
| POST   | `/api/messages/`                             | Send a new message              |
| GET    | `/api/messages/conversations/`               | List all conversations          |
| GET    | `/api/messages/conversation/<user_id>/`      | Get messages with specific user |
| POST   | `/api/messages/conversation/<user_id>/read/` | Mark messages from user as read |

### Send Message (POST `/api/messages/`)

**Request Body:**

```json
{
  "receiver_id": 2,
  "content": "Hey, what's up?"
}
```

**Response:**

```json
{
  "id": 1,
  "sender": { "id": 1, "username": "pabloPistola" },
  "receiver": { "id": 2, "username": "arthurb" },
  "content": "Hey, what's up?",
  "is_read": false,
  "created_at": "2026-01-24T10:30:00Z"
}
```

### Reseed Messages

To clear and reseed:

```bash
python manage.py seed_messages --clear
```

---

## �👥 Friends API Endpoints

All endpoints require authentication (`Authorization: Bearer <token>`)

| Method | Endpoint                             | Description                   |
| ------ | ------------------------------------ | ----------------------------- |
| GET    | `/api/friends/`                      | List your friends             |
| GET    | `/api/friends/requests/`             | Get pending incoming requests |
| POST   | `/api/friends/request/<user_id>/`    | Send friend request           |
| POST   | `/api/friends/accept/<request_id>/`  | Accept friend request         |
| POST   | `/api/friends/decline/<request_id>/` | Decline friend request        |
| DELETE | `/api/friends/remove/<user_id>/`     | Remove a friend               |

### Example Responses

#### GET `/api/friends/`

```json
[
  { "id": 2, "username": "colinw", "last_name": "Wilson" },
  { "id": 3, "username": "crystalr", "last_name": "Rodriguez" }
]
```

#### GET `/api/friends/requests/`

```json
[
  {
    "id": 5,
    "from_user": {
      "id": 4,
      "username": "nataliap",
      "first_name": "Natalia",
      "last_name": "Perez"
    },
    "created_at": "2026-01-24T10:30:00Z"
  }
]
```

#### POST `/api/friends/request/4/`

```json
{ "message": "Friend request sent" }
```

#### POST `/api/friends/accept/5/`

```json
{
  "message": "Friend request accepted",
  "friend": {
    "id": 4,
    "username": "nataliap",
    "first_name": "Natalia",
    "last_name": "Perez"
  }
}
```

---

## � Push Notifications (NEW)

Push notifications allow sending alerts to users even when the app is completely closed. This requires Web Push protocol with VAPID authentication.

### How It Works

1. **Frontend** subscribes the user's browser to push notifications
2. **Backend** stores the subscription in the database
3. When events happen (new message, friend request, etc.), backend sends a push via Web Push protocol
4. **Browser's service worker** receives the push and displays the notification

### Setup Steps

#### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs `pywebpush==2.0.0`.

#### 2. Generate VAPID Keys (One-Time)

VAPID keys are used to authenticate your server with push services.

**Option A - Using npx:**

```bash
npx web-push generate-vapid-keys
```

**Option B - Using Python:**

```bash
python -c "from py_vapid import Vapid; v = Vapid(); v.generate_keys(); print('Private:', v.private_key.to_pem().decode()); print('Public:', v.public_key.to_pem_uncompressed().decode())"
```

You'll get output like:

```
Public Key: BNx3Gu...long-string...
Private Key: YWVz...another-long-string...
```

**⚠️ IMPORTANT:** Keep the private key secret! Never commit it to git.

#### 3. Set Environment Variables

Add to your `.env` file or environment:

```bash
# Push Notifications (VAPID)
VAPID_PUBLIC_KEY=BNx3Gu...your-public-key...
VAPID_PRIVATE_KEY=YWVz...your-private-key...
```

For **Render deployment**, add these in the Environment tab.

#### 4. Run Migrations

```bash
python manage.py makemigrations notifications
python manage.py migrate
```

This creates the `PushSubscription` table.

### Push Notifications API Endpoints

| Method | Endpoint                               | Auth     | Description           |
| ------ | -------------------------------------- | -------- | --------------------- |
| GET    | `/api/notifications/vapid-public-key/` | Public   | Get VAPID public key  |
| POST   | `/api/notifications/subscribe/`        | Required | Subscribe to push     |
| POST   | `/api/notifications/unsubscribe/`      | Required | Unsubscribe from push |

#### GET `/api/notifications/vapid-public-key/`

Frontend calls this to get the public key for subscribing.

**Response:**

```json
{
  "publicKey": "BNx3Gu...your-public-key..."
}
```

#### POST `/api/notifications/subscribe/`

Subscribe a browser to push notifications.

**Request Body:**

```json
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/...",
  "keys": {
    "p256dh": "BNcRd...",
    "auth": "tBH..."
  }
}
```

**Response:**

```json
{
  "message": "Successfully subscribed to push notifications"
}
```

#### POST `/api/notifications/unsubscribe/`

**Request Body:**

```json
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/..."
}
```

### Using Push in Your Views

Import the push helper functions:

```python
from notifications.utils import (
    push_friend_request,
    push_friend_accepted,
    push_new_message,
    push_post_comment,
    push_comment_reply,
    send_push_notification  # For custom notifications
)
```

**Example - Send push when message is sent:**

```python
# In messages_app/views.py
from notifications.utils import push_new_message

def send_message(request):
    # ... create message logic ...

    # Send push notification (won't fail if user has no subscriptions)
    push_new_message(
        to_user_id=receiver.id,
        from_user=request.user,
        message_preview=message.content[:100]
    )
```

**Example - Send push for friend request:**

```python
# In friends/views.py
from notifications.utils import push_friend_request

def send_friend_request(request, user_id):
    # ... create friend request logic ...

    push_friend_request(
        to_user_id=user_id,
        from_user=request.user
    )
```

**Example - Custom push notification:**

```python
from notifications.utils import send_push_notification

send_push_notification(
    user_id=5,
    title='Custom Alert',
    body='Something happened!',
    data={'url': '/some-page', 'custom_key': 'value'},
    tag='custom-alert'  # Groups notifications with same tag
)
```

### Available Push Functions

| Function                 | Description                             |
| ------------------------ | --------------------------------------- |
| `push_friend_request`    | New friend request received             |
| `push_friend_accepted`   | Friend request was accepted             |
| `push_new_message`       | New direct message received             |
| `push_post_comment`      | Someone commented on your post          |
| `push_comment_reply`     | Someone replied to your comment         |
| `send_push_notification` | Generic push (for custom notifications) |

### Troubleshooting

**Push not working?**

1. Check `VAPID_PUBLIC_KEY` and `VAPID_PRIVATE_KEY` are set
2. Verify user has subscribed (check `PushSubscription` table)
3. Check Django logs for errors

**Test subscriptions exist:**

```bash
python manage.py shell -c "from notifications.models import PushSubscription; print(PushSubscription.objects.count(), 'subscriptions')"
```

---

## �🚀 Deployment (Render)

A `build.sh` script is included for Render deployment:

```bash
#!/usr/bin/env bash
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
```

---

## 🔍 Useful Commands

**Check users in database:**

```bash
python manage.py shell -c "from django.contrib.auth.models import User; [print(f'{u.username} | {u.email}') for u in User.objects.all()]"
```

**Run dev server:**

```bash
python manage.py runserver
```

**Create superuser for admin:**

```bash
python manage.py createsuperuser
```

**Access admin panel:**

```
http://127.0.0.1:8000/admin/
```
