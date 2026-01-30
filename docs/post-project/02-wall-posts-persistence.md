# 📝 Wall Posts Persistence Fix

> **Problem:** Posts on friend's profile walls disappear after refresh

## The Issue

When posting on another user's profile:
1. Post appears immediately ✅
2. Refresh page → Post disappears ❌
3. Only posts on your OWN profile persist

## Root Cause

The `target_profile` field existed in the database, but:
1. Serializer wasn't accepting `target_profile_id` from frontend
2. Serializer wasn't returning `target_profile` in responses

### Data Flow Problem

```
Frontend sends:
{
  "content": "Hello!",
  "type": "thoughts",
  "target_profile_id": 5    ← Backend ignored this!
}

Backend saves:
{
  "author_id": 3,
  "content": "Hello!",
  "type": "thoughts",
  "target_profile_id": NULL  ← Lost!
}
```

## The Solution

### Step 1: Model (Already existed)

```python
# backend/posts/models.py

class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    
    # Wall posts: if set, this post appears on target_profile's wall
    target_profile = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="wall_posts",
        null=True,
        blank=True,
    )
    # ... other fields
```

### Step 2: Serializer (The Fix)

```python
# backend/posts/serializers.py

from django.contrib.auth.models import User

class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    target_profile = UserSerializer(read_only=True)  # ← Returns full user object
    
    # Accept target_profile_id from frontend
    target_profile_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='target_profile',      # ← Maps to the model field
        write_only=True,
        required=False,
        allow_null=True,
    )
    
    class Meta:
        model = Post
        fields = [
            "id",
            "author",
            "content",
            "type",
            "target_profile",      # ← Read (returns user object)
            "target_profile_id",   # ← Write (accepts user ID)
            # ... other fields
        ]
        read_only_fields = ["author", "target_profile", ...]
```

### Key Concept: PrimaryKeyRelatedField

This is the magic that makes it work:

```python
target_profile_id = serializers.PrimaryKeyRelatedField(
    queryset=User.objects.all(),  # Validates ID exists
    source='target_profile',       # Saves to this model field
    write_only=True,               # Only for POST/PUT, not GET
    required=False,                # Optional field
    allow_null=True,               # Can be null
)
```

**How it works:**
1. Frontend sends `target_profile_id: 5`
2. DRF looks up `User.objects.get(id=5)`
3. If found, saves it to `post.target_profile`
4. On GET, `target_profile` returns full user object via `UserSerializer`

### Data Flow After Fix

```
Frontend sends:
{
  "content": "Hello!",
  "type": "thoughts",
  "target_profile_id": 5
}

Backend saves:
{
  "author_id": 3,
  "content": "Hello!",
  "type": "thoughts",
  "target_profile_id": 5  ← Saved!
}

Backend returns:
{
  "id": 123,
  "author": {"id": 3, "username": "quesoblanci"},
  "target_profile": {"id": 5, "username": "pabloPistola"},  ← Full object!
  "content": "Hello!",
  "type": "thoughts"
}
```

## Frontend Matching Logic

The frontend filters posts for a profile page:

```javascript
// Profile.jsx
const profilePosts = posts.filter(p => 
  p.author?.username === profileUser?.username ||        // Own posts
  p.target_profile?.id === profileUser?.id ||            // Wall posts by ID
  p.target_profile?.username === profileUser?.username   // Wall posts by username
);
```

## Migration

The migration `0007_post_target_profile.py` adds the field:

```python
# backend/posts/migrations/0007_post_target_profile.py

migrations.AddField(
    model_name='post',
    name='target_profile',
    field=models.ForeignKey(
        blank=True,
        null=True,
        on_delete=django.db.models.deletion.CASCADE,
        related_name='wall_posts',
        to=settings.AUTH_USER_MODEL
    ),
),
```

## Testing

1. Go to a friend's profile
2. Create a post via the composer
3. Post appears immediately
4. Refresh page
5. Post should still be there ✅
6. Check Django Admin → Posts → Verify `target_profile` is set

## Key Learnings

1. **Model field ≠ API field** - Just adding to the model doesn't expose it to the API
2. **Serializers control everything** - They determine what's accepted and returned
3. **PrimaryKeyRelatedField is your friend** - Handles ForeignKey relationships elegantly
4. **read_only vs write_only** - Separate concerns for input and output
5. **source parameter** - Maps a custom field name to the actual model field
