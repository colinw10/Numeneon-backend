# MyStudio Music Feature Implementation

How we built the playlist/music feature for Numeneon, allowing users to have a "currently vibing to" song and a playable playlist on their profile.

## Overview

The MyStudio feature (inspired by old MySpace) lets users:

- Set a "profile song" that plays when visiting their profile
- Build a playlist of up to 5 songs
- Search for songs with real 30-second previews
- Auto-play option for profile visitors

## The Challenge

**Problem:** We wanted users to play music, but:

1. Spotify API requires Premium + OAuth (complex, paid)
2. Can't stream full songs without licensing costs
3. Need something free and legal

**Solution:** Use **Deezer API** for:

- Free access (no API key required for basic endpoints)
- 30-second preview clips (legal for free use)
- Good catalog coverage
- Fallback to iTunes API if needed

## Architecture

### Models

```
┌─────────────────────────────────────┐
│          MySpaceProfile             │
├─────────────────────────────────────┤
│ user (OneToOne → User)              │
│ profile_song_title                  │
│ profile_song_artist                 │
│ profile_song_external_id            │
│ profile_song_preview_url ──────────────► Deezer 30-sec MP3
│ profile_song_album_art              │
│ auto_play (bool)                    │
└─────────────────────────────────────┘
              │
              │ 1:N
              ▼
┌─────────────────────────────────────┐
│           PlaylistSong              │
├─────────────────────────────────────┤
│ myspace_profile (FK)                │
│ title, artist                       │
│ duration_ms                         │
│ external_id ──────────────────────────► Deezer track ID
│ preview_url ──────────────────────────► Deezer 30-sec MP3
│ album_art                           │
│ order (for drag-drop reordering)    │
└─────────────────────────────────────┘
```

### API Endpoints

| Endpoint                          | Method | Auth | Description             |
| --------------------------------- | ------ | ---- | ----------------------- |
| `/api/mystudio/search/?q=`        | GET    | No   | Search songs via Deezer |
| `/api/mystudio/profile/`          | GET    | Yes  | Current user's profile  |
| `/api/mystudio/<username>/`       | GET    | No   | Any user's profile      |
| `/api/mystudio/`                  | PUT    | Yes  | Update profile settings |
| `/api/mystudio/playlist/`         | POST   | Yes  | Add song to playlist    |
| `/api/mystudio/playlist/<id>/`    | DELETE | Yes  | Remove song             |
| `/api/mystudio/playlist/reorder/` | POST   | Yes  | Reorder playlist        |

### Data Flow

```
┌──────────────┐     GET /search?q=tool     ┌──────────────┐
│   Frontend   │ ────────────────────────►  │   Backend    │
│              │                            │              │
│              │                            │   ┌──────────┴───────┐
│              │                            │   │ Deezer API       │
│              │                            │   │ /search?q=tool   │
│              │                            │   └──────────┬───────┘
│              │  ◄───────────────────────  │              │
│              │  [{ title, artist,         │              │
│              │     preview_url, ... }]    │              │
│              │                            │              │
│   User picks │                            │              │
│   a song     │  POST /playlist/           │              │
│              │  { title, artist,          │              │
│              │    preview_url, ... }      │              │
│              │ ────────────────────────►  │  Save to DB  │
│              │                            │              │
│   <audio>    │                            │              │
│   plays the  │ ◄── preview_url ─────────  │              │
│   30-sec clip│   (direct Deezer MP3)      │              │
└──────────────┘                            └──────────────┘
```

## Implementation Details

### 1. Search Endpoint

The search endpoint proxies Deezer's API:

```python
@api_view(['GET'])
@permission_classes([AllowAny])
def search_songs(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return Response({'error': 'Query required'}, status=400)

    resp = requests.get(f'https://api.deezer.com/search?q={query}&limit=10')
    data = resp.json()

    results = []
    for track in data.get('data', []):
        results.append({
            'id': track.get('id'),
            'title': track.get('title'),
            'artist': track.get('artist', {}).get('name'),
            'album_art': track.get('album', {}).get('cover_medium'),
            'preview_url': track.get('preview'),  # 30-sec MP3!
            'duration_ms': track.get('duration', 0) * 1000,
            'external_id': str(track.get('id')),
        })

    return Response({'results': results})
```

### 2. Adding Songs to Playlist

```python
MAX_PLAYLIST_SONGS = 5

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_song_to_playlist(request):
    profile = get_or_create_mystudio_profile(request.user)

    # Enforce limit
    if profile.playlist_songs.count() >= MAX_PLAYLIST_SONGS:
        return Response(
            {'error': f'Max {MAX_PLAYLIST_SONGS} songs allowed'},
            status=400
        )

    # Validate and save
    serializer = AddSongToPlaylistSerializer(data=request.data)
    if serializer.is_valid():
        song = PlaylistSong.objects.create(
            myspace_profile=profile,
            **serializer.validated_data
        )
        return Response(PlaylistSongSerializer(song).data, status=201)

    return Response(serializer.errors, status=400)
```

### 3. Frontend Audio Playback

Preview URLs are direct MP3 links. Frontend just uses `<audio>`:

```javascript
const audio = new Audio(song.preview_url);
audio.play();
```

Or with a player component:

```jsx
<audio src={currentSong?.preview_url} controls autoPlay={profile.auto_play} />
```

### 4. URL Routing Order (Important!)

Django URL patterns are matched in order. The `<str:username>/` pattern would catch everything, so specific routes must come FIRST:

```python
urlpatterns = [
    path('search/', views.search_songs),           # Must be before username
    path('profile/', views.get_my_mystudio_profile),
    path('playlist/', views.add_song_to_playlist),
    path('playlist/<int:song_id>/', views.remove_song_from_playlist),

    path('<str:username>/', views.get_mystudio_profile),  # LAST - catches all
]
```

## Database Considerations

### App Rename Migration

Originally named `myspace`, we renamed to `mystudio`. To avoid recreating tables:

```python
class Meta:
    db_table = 'myspace_myspaceprofile'  # Keep existing table name
```

This tells Django to use the old table name while the code uses the new app name.

### URL Field Length

Deezer preview URLs are long (~300 chars). Default URLField max is 200:

```python
# Migration to increase length
preview_url = models.URLField(max_length=500, blank=True, null=True)
```

### Production Migration

When you can't run Django migrations (table mismatch), use raw SQL:

```sql
ALTER TABLE myspace_playlistsong ALTER COLUMN preview_url TYPE VARCHAR(500);
INSERT INTO django_migrations (app, name, applied) VALUES ('mystudio', '0004_...', NOW());
```

## Why Deezer Over Other Options

| Option     | Pros                                  | Cons                           |
| ---------- | ------------------------------------- | ------------------------------ |
| **Deezer** | Free, no auth needed, 30-sec previews | URLs can expire (refresh-able) |
| Spotify    | Best catalog                          | Requires Premium + OAuth       |
| iTunes     | Stable URLs                           | Search-only, less data         |
| SoundCloud | Some full tracks                      | Inconsistent availability      |
| YouTube    | Full songs                            | Requires JS SDK, ads           |

We use Deezer as primary with iTunes as fallback (via `deezer_utils.py`).

## Frontend Integration

### Service Methods

```javascript
// myStudioService.js
export const searchSongs = (query) =>
  api.get(`/mystudio/search/?q=${encodeURIComponent(query)}`);

export const getMyStudioProfile = (username) =>
  api.get(`/mystudio/${username}/`);

export const addSongToPlaylist = (song) =>
  api.post("/mystudio/playlist/", song);

export const removeSong = (songId) =>
  api.delete(`/mystudio/playlist/${songId}/`);
```

### Audio Player Component

```jsx
function MusicPlayer({ playlist, autoPlay }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const audioRef = useRef(null);

  const currentSong = playlist[currentIndex];

  const playNext = () => {
    if (currentIndex < playlist.length - 1) {
      setCurrentIndex((i) => i + 1);
    }
  };

  return (
    <div className="music-player">
      <img src={currentSong.album_art} alt={currentSong.title} />
      <div>
        <h4>{currentSong.title}</h4>
        <p>{currentSong.artist}</p>
      </div>
      <audio
        ref={audioRef}
        src={currentSong.preview_url}
        autoPlay={autoPlay}
        onEnded={playNext}
        controls
      />
    </div>
  );
}
```

## Troubleshooting

### "Preview Unavailable"

- **Cause:** Old songs have placeholder URLs, not real Deezer URLs
- **Fix:** Delete old songs, re-add via search

### 405 Method Not Allowed on POST /playlist/

- **Cause:** URL routing order - `<str:username>/` was catching `playlist/`
- **Fix:** Move specific routes before the username wildcard

### Database Table Not Found

- **Cause:** App renamed but tables still have old names
- **Fix:** Add `db_table` to Meta class

### Long URLs Truncated

- **Cause:** URLField default max_length=200
- **Fix:** Set `max_length=500` and migrate

## Summary

1. **Deezer API** provides free 30-second preview clips
2. **Backend** proxies search, stores song metadata with preview URLs
3. **Frontend** plays preview URLs directly with `<audio>`
4. **Max 5 songs** per playlist enforced server-side
5. **URL routing order** matters - specific routes before wildcards
