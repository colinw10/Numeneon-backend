# Numeneon Models Overview

Complete breakdown of all Django models in the Numeneon backend.

## Summary

| App               | Models                          | Description                             |
| ----------------- | ------------------------------- | --------------------------------------- |
| **users**         | Profile                         | User profile data (avatar, bio)         |
| **posts**         | Post, Like                      | Social media posts and likes            |
| **friends**       | Friendship, FriendRequest       | Friend connections and requests         |
| **messages_app**  | Message                         | Direct messaging                        |
| **stories**       | Story, StoryView, StoryReaction | Instagram-style 24hr stories            |
| **notifications** | PushSubscription                | Browser push notification subscriptions |
| **mystudio**      | MySpaceProfile, PlaylistSong    | Music profile and playlist feature      |

**Total: 12 models** across 7 apps (plus Django's built-in User model).

---

## 1. Users App

### Profile

Extends Django's built-in User model with additional profile data.

```python
class Profile(models.Model):
    user = OneToOneField(User)      # Links to Django User
    avatar = URLField               # Cloudinary profile picture URL
    bio = TextField(max_length=500) # User bio
    location = CharField            # User's location
    website = URLField              # User's website
    created_at = DateTimeField      # When profile created
    updated_at = DateTimeField      # Last modified
```

**Relationships:**

- `User.profile` → Get user's profile via related_name

**Notes:**

- Auto-created via signal when User is created
- Avatar stored as Cloudinary URL (uploaded by frontend)

---

## 2. Posts App

### Post

The core social media post model. Supports thoughts, media, milestones, wall posts, comments, and threaded replies.

```python
class Post(models.Model):
    POST_TYPES = ['thoughts', 'media', 'milestones']

    author = ForeignKey(User)           # Who wrote it
    target_profile = ForeignKey(User)   # Wall post target (nullable)
    type = CharField                     # Post type
    content = TextField(max_length=500) # Post text
    media_url = URLField                 # Image/video URL
    parent = ForeignKey('self')          # For comments (reply to post)
    reply_to_comment = ForeignKey('self')# Threaded reply to comment
    mentioned_user = ForeignKey(User)    # @mention in reply
    created_at = DateTimeField
    updated_at = DateTimeField
    likes_count = IntegerField           # Denormalized count
    comment_count = IntegerField         # Denormalized count
    shares_count = IntegerField          # Denormalized count
```

**Relationships:**

- `User.posts` → All posts authored by user
- `User.wall_posts` → Posts on user's wall (by others)
- `Post.replies` → Comments on a post
- `Post.comment_replies` → Threaded replies to a comment

**Notes:**

- `parent=null` means top-level post
- `parent` set means it's a comment
- `reply_to_comment` allows nested threading
- `target_profile` enables "wall posts" (posting on someone else's profile)

### Like

Tracks which users liked which posts.

```python
class Like(models.Model):
    user = ForeignKey(User)
    post = ForeignKey(Post)
    created_at = DateTimeField

    class Meta:
        unique_together = ('user', 'post')  # One like per user per post
```

**Relationships:**

- `User.likes` → All likes by user
- `Post.likes` → All likes on a post

---

## 3. Friends App

### Friendship

Represents an established friendship (directional - stored twice for mutual friendships).

```python
class Friendship(models.Model):
    user = ForeignKey(User)    # The user
    friend = ForeignKey(User)  # Their friend
    created_at = DateTimeField

    class Meta:
        unique_together = ('user', 'friend')
```

**Relationships:**

- `User.friendships` → User's friendships (outgoing)
- `User.friends_of` → Who has friended this user

**Notes:**

- Directional model: A→B means A considers B a friend
- For mutual friendships, both A→B and B→A records exist
- Created when friend request is accepted

### FriendRequest

Pending friend request between users.

```python
class FriendRequest(models.Model):
    from_user = ForeignKey(User)  # Who sent request
    to_user = ForeignKey(User)    # Who received request
    created_at = DateTimeField

    class Meta:
        unique_together = ('from_user', 'to_user')
```

**Relationships:**

- `User.sent_requests` → Requests this user sent
- `User.received_requests` → Requests this user received

**Notes:**

- No `status` field - request exists or it doesn't
- Accepting: creates Friendship records, deletes FriendRequest
- Declining: just deletes the FriendRequest

---

## 4. Messages App

### Message

Direct messages between users.

```python
class Message(models.Model):
    sender = ForeignKey(User)
    receiver = ForeignKey(User)
    content = TextField
    is_read = BooleanField(default=False)
    created_at = DateTimeField
    reply_to_story = ForeignKey(Story)  # Optional: story reply
```

**Relationships:**

- `User.sent_messages` → Messages sent by user
- `User.received_messages` → Messages received by user
- `Story.replies` → Messages that are replies to this story

**Notes:**

- `reply_to_story` enables "Replied to your story" feature
- `is_read` tracks whether receiver has seen the message

---

## 5. Stories App

### Story

Instagram-style stories that expire after 24 hours.

```python
class Story(models.Model):
    MEDIA_TYPES = ['image', 'video']

    id = UUIDField(primary_key=True)  # UUID instead of auto-increment
    user = ForeignKey(User)
    media_url = URLField              # Cloudinary URL
    media_type = CharField            # 'image' or 'video'
    caption = TextField(max_length=200)
    created_at = DateTimeField
    expires_at = DateTimeField        # Auto-set to created_at + 24hrs
```

**Relationships:**

- `User.stories` → All stories by user

**Properties:**

- `is_expired` → Returns True if story has expired

**Notes:**

- Uses UUID for ID (better for distributed systems)
- `expires_at` auto-calculated on save
- Frontend should filter out expired stories

### StoryView

Tracks who has viewed a story.

```python
class StoryView(models.Model):
    story = ForeignKey(Story)
    viewer = ForeignKey(User)
    viewed_at = DateTimeField

    class Meta:
        unique_together = ['story', 'viewer']
```

**Relationships:**

- `Story.views` → All views on a story
- `User.viewed_stories` → Stories this user has viewed

### StoryReaction

Reactions to stories (heart or thunder).

```python
class StoryReaction(models.Model):
    REACTIONS = ['heart', 'thunder']

    story = ForeignKey(Story)
    user = ForeignKey(User)
    reaction_type = CharField
    created_at = DateTimeField

    class Meta:
        unique_together = ['story', 'user']  # One reaction per user
```

**Relationships:**

- `Story.reactions` → All reactions on a story
- `User.story_reactions` → Reactions this user has made

---

## 6. Notifications App

### PushSubscription

Browser push notification subscriptions for PWA support.

```python
class PushSubscription(models.Model):
    user = ForeignKey(User)
    endpoint = URLField(unique=True)  # Push service endpoint
    p256dh = CharField                 # Encryption key
    auth = CharField                   # Auth secret
    created_at = DateTimeField
```

**Relationships:**

- `User.push_subscriptions` → User's browser subscriptions

**Methods:**

- `to_subscription_info()` → Returns data for pywebpush library

**Notes:**

- One user can have multiple subscriptions (multiple devices)
- Endpoint is unique per browser/device

---

## 7. MyStudio App (Music Feature)

### MySpaceProfile

Extended profile for music/playlist feature.

```python
class MySpaceProfile(models.Model):
    user = OneToOneField(User)
    avatar = CharField(default='default')  # Avatar key

    # Profile song ("currently vibing to")
    profile_song_title = CharField
    profile_song_artist = CharField
    profile_song_external_id = CharField   # Deezer track ID
    profile_song_preview_url = URLField    # 30-sec preview URL
    profile_song_album_art = URLField      # Album cover

    auto_play = BooleanField(default=False)
    created_at = DateTimeField
    updated_at = DateTimeField

    class Meta:
        db_table = 'myspace_myspaceprofile'  # Legacy table name
```

**Relationships:**

- `User.myspace_profile` → User's MyStudio profile

**Notes:**

- Separate from main Profile model (different purpose)
- `db_table` set to preserve existing table after app rename

### PlaylistSong

Songs in a user's playlist (max 5 songs).

```python
class PlaylistSong(models.Model):
    myspace_profile = ForeignKey(MySpaceProfile)
    title = CharField
    artist = CharField
    duration_ms = IntegerField
    external_id = CharField         # Deezer track ID
    preview_url = URLField          # 30-sec Deezer preview
    album_art = URLField            # Album cover
    order = PositiveIntegerField    # Playlist position
    created_at = DateTimeField

    class Meta:
        db_table = 'myspace_playlistsong'
        ordering = ['order', 'created_at']
```

**Relationships:**

- `MySpaceProfile.playlist_songs` → All songs in playlist

**Properties:**

- `duration_formatted` → "3:45" format

**Notes:**

- Preview URLs are 30-second clips from Deezer API
- `order` field enables drag-and-drop reordering
- Backend enforces max 5 songs via `MAX_PLAYLIST_SONGS`

---

## Entity Relationship Diagram

```
┌─────────┐       ┌─────────────┐       ┌──────────────────┐
│  User   │──1─1──│   Profile   │       │  MySpaceProfile  │
│ (Django)│       └─────────────┘       └────────┬─────────┘
│         │                                      │
│         │──1─1──────────────────────────────────┘
│         │
│         │──1─N──┌──────────┐
│         │       │   Post   │──1─N──┌────────┐
│         │       │          │       │  Like  │
│         │       └────┬─────┘       └────────┘
│         │            │ (self-ref for comments)
│         │
│         │──1─N──┌──────────────┐
│         │       │ Friendship   │
│         │       └──────────────┘
│         │
│         │──1─N──┌───────────────┐
│         │       │ FriendRequest │
│         │       └───────────────┘
│         │
│         │──1─N──┌──────────┐──1─N──┌───────────┐
│         │       │  Story   │       │ StoryView │
│         │       │          │       └───────────┘
│         │       │          │──1─N──┌────────────────┐
│         │       └──────────┘       │ StoryReaction  │
│         │                          └────────────────┘
│         │──1─N──┌──────────┐
│         │       │ Message  │
│         │       └──────────┘
│         │
│         │──1─N──┌──────────────────┐
│         │       │ PushSubscription │
│         │       └──────────────────┘
└─────────┘

MySpaceProfile ──1─N── PlaylistSong
```

---

## Common Patterns Used

### 1. OneToOneField for Extending User

```python
user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
```

Used by: Profile, MySpaceProfile

### 2. ForeignKey for Ownership

```python
user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
```

Used by: Post, Story, Message, Friendship, etc.

### 3. Self-Referential ForeignKey for Hierarchies

```python
parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, related_name='replies')
```

Used by: Post (for comments and threaded replies)

### 4. unique_together for Preventing Duplicates

```python
class Meta:
    unique_together = ('user', 'post')
```

Used by: Like, Friendship, FriendRequest, StoryView, StoryReaction

### 5. Timestamps

```python
created_at = models.DateTimeField(auto_now_add=True)
updated_at = models.DateTimeField(auto_now=True)
```

Used by: All models

### 6. Denormalized Counts

```python
likes_count = models.IntegerField(default=0)
```

Used by: Post (avoids expensive COUNT queries)
