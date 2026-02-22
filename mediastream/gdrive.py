"""
Google Drive Service cho MediaStream
Lấy video từ Google Drive và stream/cache trên VPS

Hỗ trợ 2 chế độ xác thực:
1. API Key (đơn giản, chỉ cho file public)
2. Service Account (linh hoạt, cho cả file private)

Luồng hoạt động:
  Client → Server → [Cache check] → Google Drive API → Cache → Stream to Client

Bảo mật:
- File Google Drive phải được chia sẻ "Anyone with the link" hoặc với service account
- Server proxy stream → client không bao giờ thấy Google Drive URL trực tiếp
- Referrer protection vẫn hoạt động như local storage
"""

import os
import re
import logging
import hashlib
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, Generator

from django.conf import settings

logger = logging.getLogger(__name__)

# Cache directory for Google Drive files
GDRIVE_CACHE_DIR = os.path.join(settings.MEDIA_ROOT, 'gdrive_cache')

# Maximum cache size (default: 10GB)
GDRIVE_CACHE_MAX_SIZE = getattr(settings, 'GDRIVE_CACHE_MAX_SIZE', 10 * 1024 * 1024 * 1024)

# Cache TTL (default: 7 days in seconds)
GDRIVE_CACHE_TTL = getattr(settings, 'GDRIVE_CACHE_TTL', 7 * 24 * 3600)

# Chunk size for streaming from Google Drive (1MB)
GDRIVE_CHUNK_SIZE = 1024 * 1024


def get_google_api_key() -> Optional[str]:
    """Get Google API key from SiteConfiguration"""
    try:
        from core.models import SiteConfiguration
        config = SiteConfiguration.get_solo()
        # Reuse YouTube API key (cùng Google project)
        return config.youtube_api_key or None
    except Exception:
        return None


def get_gdrive_service():
    """
    Get Google Drive service client.
    Uses API key for public files (simple, no credentials file needed).
    """
    try:
        from googleapiclient.discovery import build
        api_key = get_google_api_key()
        if not api_key:
            logger.warning("No Google API key configured in SiteConfiguration")
            return None
        return build('drive', 'v3', developerKey=api_key)
    except ImportError:
        logger.error("google-api-python-client not installed")
        return None
    except Exception as e:
        logger.error(f"Failed to create Google Drive service: {e}")
        return None


def extract_file_id(url_or_id: str) -> str:
    """Extract Google Drive file ID from various URL formats"""
    patterns = [
        r'/file/d/([a-zA-Z0-9_-]+)',
        r'[?&]id=([a-zA-Z0-9_-]+)',
        r'uc\?.*id=([a-zA-Z0-9_-]+)',
        r'^([a-zA-Z0-9_-]{20,})$',
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id.strip())
        if match:
            return match.group(1)
    return url_or_id.strip()


def get_file_metadata(file_id: str) -> Optional[Dict[str, Any]]:
    """
    Get file metadata from Google Drive.
    Returns: dict with name, mimeType, size, etc.
    """
    service = get_gdrive_service()
    if not service:
        return None
    
    try:
        metadata = service.files().get(
            fileId=file_id,
            fields='id,name,mimeType,size,videoMediaMetadata,imageMediaMetadata'
        ).execute()
        return metadata
    except Exception as e:
        logger.error(f"Failed to get file metadata for {file_id}: {e}")
        return None


# ============================================================================
# Cache Management
# ============================================================================

def ensure_cache_dir():
    """Ensure cache directory exists"""
    Path(GDRIVE_CACHE_DIR).mkdir(parents=True, exist_ok=True)


def get_cache_path(file_id: str) -> str:
    """Get local cache file path for a Google Drive file"""
    ensure_cache_dir()
    # Use hash of file_id as filename to avoid path issues
    safe_name = hashlib.md5(file_id.encode()).hexdigest()
    return os.path.join(GDRIVE_CACHE_DIR, safe_name)


def get_cache_meta_path(file_id: str) -> str:
    """Get metadata file path for cached file"""
    return get_cache_path(file_id) + '.meta.json'


def is_cached(file_id: str) -> bool:
    """Check if file is cached and not expired"""
    cache_path = get_cache_path(file_id)
    meta_path = get_cache_meta_path(file_id)
    
    if not os.path.exists(cache_path):
        return False
    
    # Check TTL
    if os.path.exists(meta_path):
        try:
            with open(meta_path, 'r') as f:
                meta = json.load(f)
            cached_at = meta.get('cached_at', 0)
            if time.time() - cached_at > GDRIVE_CACHE_TTL:
                # Expired
                _remove_cached(file_id)
                return False
        except (json.JSONDecodeError, OSError):
            pass
    
    return True


def get_cache_size() -> int:
    """Get total cache size in bytes"""
    ensure_cache_dir()
    total = 0
    for f in Path(GDRIVE_CACHE_DIR).iterdir():
        if f.is_file():
            total += f.stat().st_size
    return total


def _remove_cached(file_id: str):
    """Remove a cached file"""
    cache_path = get_cache_path(file_id)
    meta_path = get_cache_meta_path(file_id)
    for p in [cache_path, meta_path]:
        try:
            os.remove(p)
        except OSError:
            pass


def evict_cache_if_needed(needed_bytes: int = 0):
    """
    Evict oldest cached files if total cache exceeds limit.
    LRU strategy: remove files with oldest access time.
    """
    ensure_cache_dir()
    
    current_size = get_cache_size()
    if current_size + needed_bytes <= GDRIVE_CACHE_MAX_SIZE:
        return
    
    # Collect all cached files with their access times
    files = []
    for f in Path(GDRIVE_CACHE_DIR).iterdir():
        if f.is_file() and not f.name.endswith('.meta.json'):
            files.append((f, f.stat().st_atime, f.stat().st_size))
    
    # Sort by access time (oldest first)
    files.sort(key=lambda x: x[1])
    
    # Remove until we have enough space
    for fp, _, fsize in files:
        if current_size + needed_bytes <= GDRIVE_CACHE_MAX_SIZE:
            break
        try:
            file_id_hash = fp.stem
            meta_path = fp.with_suffix('.meta.json')
            fp.unlink(missing_ok=True)
            meta_path.unlink(missing_ok=True)
            current_size -= fsize
            logger.info(f"Evicted cached file: {fp.name}")
        except OSError as e:
            logger.warning(f"Failed to evict {fp.name}: {e}")


def save_file_meta(file_id: str, metadata: Dict[str, Any]):
    """Save metadata for cached file"""
    meta_path = get_cache_meta_path(file_id)
    meta = {
        'file_id': file_id,
        'cached_at': time.time(),
        **metadata,
    }
    try:
        with open(meta_path, 'w') as f:
            json.dump(meta, f)
    except OSError as e:
        logger.warning(f"Failed to save cache meta: {e}")


def get_cached_file_size(file_id: str) -> Optional[int]:
    """Get cached file size or None"""
    cache_path = get_cache_path(file_id)
    if os.path.exists(cache_path):
        return os.path.getsize(cache_path)
    return None


# ============================================================================
# Download & Stream from Google Drive
# ============================================================================

def download_to_cache(file_id: str) -> Optional[str]:
    """
    Download file from Google Drive to local cache.
    Returns: local file path or None on failure.
    
    Uses chunks for large files to avoid memory issues.
    """
    service = get_gdrive_service()
    if not service:
        return None
    
    # Check if already cached
    cache_path = get_cache_path(file_id)
    if is_cached(file_id):
        logger.info(f"Cache hit: {file_id}")
        # Update access time
        os.utime(cache_path, None)
        return cache_path
    
    logger.info(f"Cache miss, downloading from Google Drive: {file_id}")
    
    try:
        from googleapiclient.http import MediaIoBaseDownload
        import io
        
        # Get file metadata first
        metadata = get_file_metadata(file_id)
        file_size = int(metadata.get('size', 0)) if metadata else 0
        
        # Evict cache if needed
        if file_size > 0:
            evict_cache_if_needed(file_size)
        
        # Download file
        request = service.files().get_media(fileId=file_id)
        
        with open(cache_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request, chunksize=GDRIVE_CHUNK_SIZE)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    logger.debug(f"Download {file_id}: {int(status.progress() * 100)}%")
        
        # Save metadata
        save_file_meta(file_id, {
            'name': metadata.get('name', '') if metadata else '',
            'mime_type': metadata.get('mimeType', '') if metadata else '',
            'size': file_size,
        })
        
        logger.info(f"Downloaded to cache: {file_id} ({file_size} bytes)")
        return cache_path
        
    except Exception as e:
        logger.error(f"Failed to download {file_id} from Google Drive: {e}")
        # Clean up partial download
        try:
            os.remove(cache_path)
        except OSError:
            pass
        return None


def stream_from_gdrive_direct(file_id: str, range_start: int = 0, range_end: int = None) -> Optional[Generator[bytes, None, None]]:
    """
    Stream directly from Google Drive without caching.
    Useful for very large files or first-time access.
    
    Returns: generator of chunks or None on failure.
    """
    service = get_gdrive_service()
    if not service:
        return None
    
    try:
        from googleapiclient.http import HttpRequest
        import httplib2
        
        # Build range header
        headers = {}
        if range_start or range_end:
            if range_end:
                headers['Range'] = f'bytes={range_start}-{range_end}'
            else:
                headers['Range'] = f'bytes={range_start}-'
        
        # Get download URL
        request = service.files().get_media(fileId=file_id)
        request.headers.update(headers)
        
        # Execute and get response body
        http = service._http
        response, content = http.request(request.uri, method='GET', headers=request.headers)
        
        if response.status in (200, 206):
            # Return content in chunks
            chunk_size = 8192
            for i in range(0, len(content), chunk_size):
                yield content[i:i + chunk_size]
        else:
            logger.error(f"Google Drive API returned {response.status} for {file_id}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to stream {file_id}: {e}")
        return None


def get_gdrive_file_info(file_id: str) -> Optional[Dict[str, Any]]:
    """
    Get comprehensive file info from Google Drive.
    Returns dict with: name, mime_type, size, video_metadata
    """
    metadata = get_file_metadata(file_id)
    if not metadata:
        return None
    
    info = {
        'name': metadata.get('name', ''),
        'mime_type': metadata.get('mimeType', ''),
        'size': int(metadata.get('size', 0)),
    }
    
    # Video metadata (duration, width, height)
    video_meta = metadata.get('videoMediaMetadata', {})
    if video_meta:
        info['duration_ms'] = int(video_meta.get('durationMillis', 0))
        info['duration'] = info['duration_ms'] // 1000 if info['duration_ms'] else None
        info['width'] = int(video_meta.get('width', 0)) or None
        info['height'] = int(video_meta.get('height', 0)) or None
    
    return info


# ============================================================================
# Admin Helper Functions
# ============================================================================

def import_from_gdrive_url(url: str) -> Dict[str, Any]:
    """
    Import media from Google Drive URL.
    Returns dict with all metadata for creating StreamMedia.
    
    Usage in admin:
        info = import_from_gdrive_url("https://drive.google.com/file/d/xxx/view")
        media = StreamMedia(
            title=info['title'],
            storage_type='gdrive',
            gdrive_file_id=info['file_id'],
            gdrive_url=url,
            **info['metadata']
        )
    """
    file_id = extract_file_id(url)
    if not file_id:
        return {'error': 'Could not extract file ID from URL'}
    
    info = get_gdrive_file_info(file_id)
    if not info:
        return {'error': f'Could not get file info for ID: {file_id}'}
    
    # Determine media type from mime
    mime_type = info.get('mime_type', '')
    if 'video' in mime_type:
        media_type = 'video'
    elif 'audio' in mime_type:
        media_type = 'audio'
    else:
        media_type = 'video'  # Default
    
    # Clean title from filename
    title = info.get('name', 'Untitled')
    # Remove file extension
    title = os.path.splitext(title)[0]
    # Clean up common patterns
    title = title.replace('_', ' ').replace('-', ' ')
    
    result = {
        'file_id': file_id,
        'title': title,
        'metadata': {
            'media_type': media_type,
            'mime_type': mime_type,
            'file_size': info.get('size', 0),
            'duration': info.get('duration'),
            'width': info.get('width'),
            'height': info.get('height'),
        }
    }
    
    return result
