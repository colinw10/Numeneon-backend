"""
Utility functions for fetching music preview URLs.
Supports iTunes (primary - stable URLs) and Deezer (fallback).
"""
import json
import urllib.request
import urllib.error
import urllib.parse
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def get_itunes_preview_url(title: str, artist: str) -> Optional[str]:
    """
    Fetch preview URL from iTunes API by searching for title + artist.
    iTunes URLs are stable and don't expire like Deezer's.
    
    Returns:
        Preview URL string or None if not found
    """
    try:
        query = urllib.parse.quote(f"{title} {artist}")
        url = f'https://itunes.apple.com/search?term={query}&media=music&limit=1'
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; Numeneon/1.0)'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                results = data.get('results', [])
                if results:
                    preview = results[0].get('previewUrl')
                    if preview:
                        logger.info(f"Found iTunes preview for '{title}' by '{artist}'")
                        return preview
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError) as e:
        logger.warning(f"iTunes API error for '{title}': {e}")
    
    return None


def get_deezer_preview_url(track_id: str) -> Optional[str]:
    """
    Fetch a fresh preview URL from Deezer API for a given track ID.
    Note: Deezer URLs contain signed tokens that can expire.
    
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
                    logger.info(f"Fetched Deezer preview for track {track_id}")
                    return preview
    except urllib.error.HTTPError as e:
        logger.warning(f"Deezer API HTTP error for track {track_id}: {e.code}")
    except urllib.error.URLError as e:
        logger.warning(f"Deezer API URL error for track {track_id}: {e.reason}")
    except (json.JSONDecodeError, TimeoutError) as e:
        logger.warning(f"Deezer API error for track {track_id}: {e}")
    
    return None


def get_preview_url(title: str, artist: str, external_id: str = None) -> Optional[str]:
    """
    Get preview URL using iTunes (primary) with Deezer fallback.
    iTunes URLs are more stable and don't expire.
    
    Args:
        title: Song title
        artist: Artist name
        external_id: Optional Deezer track ID for fallback
    
    Returns:
        Preview URL or None
    """
    # Try iTunes first (more stable URLs)
    preview = get_itunes_preview_url(title, artist)
    if preview:
        return preview
    
    # Fallback to Deezer if we have a track ID
    if external_id and external_id.startswith('deezer:'):
        preview = get_deezer_preview_url(external_id)
        if preview:
            return preview
    
    return None
