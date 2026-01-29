"""
Utility functions for fetching fresh Deezer preview URLs.
Deezer preview URLs contain signed tokens that expire,
so we need to fetch them fresh when serving to the frontend.
"""
import requests
from typing import Optional


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
        response = requests.get(
            f'https://api.deezer.com/track/{track_id}',
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('preview')
    except requests.RequestException:
        pass
    
    return None


def get_deezer_track_info(track_id: str) -> dict:
    """
    Fetch complete track info from Deezer API.
    
    Returns dict with preview, title, artist, duration, album_art
    """
    if track_id.startswith('deezer:track:'):
        track_id = track_id.split(':')[-1]
    
    try:
        response = requests.get(
            f'https://api.deezer.com/track/{track_id}',
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return {
                'preview_url': data.get('preview'),
                'title': data.get('title'),
                'artist': data.get('artist', {}).get('name'),
                'duration_ms': data.get('duration', 0) * 1000,
                'album_art': data.get('album', {}).get('cover_big'),
            }
    except requests.RequestException:
        pass
    
    return {}
