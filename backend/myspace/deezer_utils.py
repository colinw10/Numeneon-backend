"""
Utility functions for fetching fresh Deezer preview URLs.
Deezer preview URLs contain signed tokens that expire,
so we need to fetch them fresh when serving to the frontend.
"""
import json
import urllib.request
import urllib.error
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def get_deezer_preview_url(track_id: str) -> Optional[str]:
    """
    Fetch a fresh preview URL from Deezer API for a given track ID.
    
    Args:
        track_id: Deezer track ID (e.g., "740969222" or "deezer:track:740969222")
    
    Returns:
        Fresh preview URL string or None if not found
    """
    # Extract numeric ID if prefixed
    if track_id.startswith('deezer:track:'):
        track_id = track_id.split(':')[-1]
    
    try:
        url = f'https://api.deezer.com/track/{track_id}'
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; Numeneon/1.0)'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                preview = data.get('preview')
                if preview:
                    logger.info(f"Fetched preview URL for track {track_id}")
                    return preview
    except urllib.error.HTTPError as e:
        logger.warning(f"Deezer API HTTP error for track {track_id}: {e.code}")
    except urllib.error.URLError as e:
        logger.warning(f"Deezer API URL error for track {track_id}: {e.reason}")
    except (json.JSONDecodeError, TimeoutError) as e:
        logger.warning(f"Deezer API error for track {track_id}: {e}")
    
    return None


def get_deezer_track_info(track_id: str) -> dict:
    """
    Fetch complete track info from Deezer API.
    
    Returns dict with preview, title, artist, duration, album_art
    """
    if track_id.startswith('deezer:track:'):
        track_id = track_id.split(':')[-1]
    
    try:
        url = f'https://api.deezer.com/track/{track_id}'
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; Numeneon/1.0)'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                return {
                    'preview_url': data.get('preview'),
                    'title': data.get('title'),
                    'artist': data.get('artist', {}).get('name'),
                    'duration_ms': data.get('duration', 0) * 1000,
                    'album_art': data.get('album', {}).get('cover_big'),
                }
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError) as e:
        logger.warning(f"Deezer API error for track {track_id}: {e}")
    
    return {}
