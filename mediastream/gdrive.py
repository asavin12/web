"""
Google Drive Service cho MediaStream
Lấy video từ Google Drive và stream/cache trên VPS

Phương pháp: Direct HTTP download — KHÔNG cần API Key hay Service Account.
Chỉ yêu cầu file được chia sẻ "Anyone with the link can view".

Luồng hoạt động:
  Client → Server (referrer check) → [Cache check] → Google Drive download → Cache → Stream

Bảo mật:
- Server proxy stream → client không bao giờ thấy Google Drive URL
- Referrer protection vẫn hoạt động như local storage
- Google Drive chỉ thấy request từ VPS IP, không phải từ user
"""

import os
import re
import logging
import hashlib
import json
import time
import mimetypes
from pathlib import Path
from typing import Optional, Dict, Any

import requests

from django.conf import settings

logger = logging.getLogger(__name__)

# Cache directory for Google Drive files
GDRIVE_CACHE_DIR = os.path.join(settings.MEDIA_ROOT, 'gdrive_cache')

# Maximum cache size (default: 10GB)
GDRIVE_CACHE_MAX_SIZE = getattr(settings, 'GDRIVE_CACHE_MAX_SIZE', 10 * 1024 * 1024 * 1024)

# Cache TTL (default: 7 days in seconds)
GDRIVE_CACHE_TTL = getattr(settings, 'GDRIVE_CACHE_TTL', 7 * 24 * 3600)

# Chunk size for download (1MB)
GDRIVE_CHUNK_SIZE = 1024 * 1024

# Google Drive direct download URL (new domain since ~2024)
GDRIVE_DOWNLOAD_URL = 'https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t'

# Fallback: old URL format (may redirect to new domain)
GDRIVE_DOWNLOAD_URL_OLD = 'https://drive.google.com/uc?export=download&id={file_id}'

# User agent to avoid blocks
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'


def extract_file_id(url_or_id: str) -> str:
    """
    Extract Google Drive file ID from various URL formats.
    
    Supports:
    - https://drive.google.com/file/d/FILE_ID/view
    - https://drive.google.com/open?id=FILE_ID
    - https://drive.google.com/uc?id=FILE_ID
    - https://drive.google.com/uc?export=download&id=FILE_ID
    - Raw FILE_ID string (20+ chars)
    """
    patterns = [
        r'/file/d/([a-zA-Z0-9_-]+)',
        r'[?&]id=([a-zA-Z0-9_-]+)',
        r'^([a-zA-Z0-9_-]{20,})$',
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id.strip())
        if match:
            return match.group(1)
    return url_or_id.strip()


# ============================================================================
# Cache Management
# ============================================================================

def ensure_cache_dir():
    """Ensure cache directory exists"""
    Path(GDRIVE_CACHE_DIR).mkdir(parents=True, exist_ok=True)


def get_cache_path(file_id: str) -> str:
    """Get local cache file path for a Google Drive file"""
    ensure_cache_dir()
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
    
    # File must be non-empty
    if os.path.getsize(cache_path) == 0:
        _remove_cached(file_id)
        return False
    
    # Check TTL
    if os.path.exists(meta_path):
        try:
            with open(meta_path, 'r') as f:
                meta = json.load(f)
            cached_at = meta.get('cached_at', 0)
            if time.time() - cached_at > GDRIVE_CACHE_TTL:
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
    
    files = []
    for f in Path(GDRIVE_CACHE_DIR).iterdir():
        if f.is_file() and not f.name.endswith('.meta.json'):
            files.append((f, f.stat().st_atime, f.stat().st_size))
    
    # Sort by access time (oldest first)
    files.sort(key=lambda x: x[1])
    
    for fp, _, fsize in files:
        if current_size + needed_bytes <= GDRIVE_CACHE_MAX_SIZE:
            break
        try:
            meta_path = fp.parent / (fp.name + '.meta.json')
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
            json.dump(meta, f, indent=2)
    except OSError as e:
        logger.warning(f"Failed to save cache meta: {e}")


def get_cached_meta(file_id: str) -> Optional[Dict[str, Any]]:
    """Get cached metadata or None"""
    meta_path = get_cache_meta_path(file_id)
    if os.path.exists(meta_path):
        try:
            with open(meta_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return None


# ============================================================================
# Download from Google Drive (Direct HTTP - NO API Key needed)
# ============================================================================

def _get_confirm_token(response: requests.Response) -> Optional[str]:
    """
    Extract confirmation token for large file download.
    Google shows a warning page for files > ~100MB.
    """
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    
    # Check HTML content for confirmation token
    if 'confirm=t' in response.text:
        return 't'
    
    # Check for virus scan warning
    if 'Google Drive - Virus scan warning' in response.text or 'Too large for Google' in response.text:
        return 't'
    
    return None


def download_to_cache(file_id: str) -> Optional[str]:
    """
    Download file from Google Drive to local cache.
    Returns: local file path or None on failure.
    
    Handles:
    - New domain (drive.usercontent.google.com) with confirm=t
    - Fallback to old domain (drive.google.com/uc) with virus scan bypass
    - Chunked download for memory efficiency
    """
    cache_path = get_cache_path(file_id)
    
    # Check cache first
    if is_cached(file_id):
        logger.info(f"Cache hit: {file_id}")
        os.utime(cache_path, None)  # Update access time
        return cache_path
    
    logger.info(f"Cache miss, downloading from Google Drive: {file_id}")
    
    session = requests.Session()
    session.headers.update({'User-Agent': USER_AGENT})
    
    try:
        # Step 1: Try new domain first (drive.usercontent.google.com)
        url = GDRIVE_DOWNLOAD_URL.format(file_id=file_id)
        response = session.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        content_type = response.headers.get('Content-Type', '')
        
        # Step 2: If new URL returned HTML, try old URL with confirm flow
        if 'text/html' in content_type:
            logger.info(f"New URL returned HTML, trying old URL for {file_id}")
            response.close()
            
            url = GDRIVE_DOWNLOAD_URL_OLD.format(file_id=file_id)
            response = session.get(url, stream=True, timeout=60)
            response.raise_for_status()
            content_type = response.headers.get('Content-Type', '')
            
            if 'text/html' in content_type:
                # Parse the virus scan warning page for the actual download form
                html = response.text
                token = _get_confirm_token(response)
                
                # Extract form action URL (new Google pattern)
                import re as _re
                form_action = _re.search(r'action="([^"]+)"', html)
                
                if form_action:
                    # Use the form action URL with confirm params
                    confirm_url = form_action.group(1)
                    # Add query params from form
                    params = {}
                    for inp in _re.finditer(r'name="([^"]+)"\s+value="([^"]+)"', html):
                        params[inp.group(1)] = inp.group(2)
                    
                    logger.info(f"Using form action URL: {confirm_url} with params: {list(params.keys())}")
                    response = session.get(confirm_url, params=params, stream=True, timeout=60)
                    response.raise_for_status()
                    content_type = response.headers.get('Content-Type', '')
                
                if 'text/html' in content_type:
                    logger.error(f"Still getting HTML for {file_id}. "
                                 f"File may not be shared publicly.")
                    return None
        
        # Step 3: Get file size from headers
        file_size = int(response.headers.get('Content-Length', 0))
        actual_content_type = content_type
        
        # Get filename from Content-Disposition if available
        filename = ''
        cd = response.headers.get('Content-Disposition', '')
        if cd:
            fname_match = re.search(r"filename\*?=['\"]?(?:UTF-8'')?([^'\";\n]+)", cd)
            if fname_match:
                filename = fname_match.group(1).strip()
        
        logger.info(f"Downloading: {filename or file_id} ({file_size} bytes, {actual_content_type})")
        
        # Evict cache if needed
        if file_size > 0:
            evict_cache_if_needed(file_size)
        
        # Step 4: Download in chunks
        downloaded = 0
        with open(cache_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=GDRIVE_CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if file_size > 0 and downloaded % (5 * GDRIVE_CHUNK_SIZE) == 0:
                        pct = int(downloaded / file_size * 100)
                        logger.debug(f"Download {file_id}: {pct}% ({downloaded}/{file_size})")
        
        # Verify download
        actual_size = os.path.getsize(cache_path)
        if actual_size == 0:
            logger.error(f"Downloaded file is empty: {file_id}")
            os.remove(cache_path)
            return None
        
        # Guess mime type from filename
        mime_type = actual_content_type
        if filename:
            guessed = mimetypes.guess_type(filename)[0]
            if guessed:
                mime_type = guessed
        
        # Save metadata
        save_file_meta(file_id, {
            'filename': filename,
            'mime_type': mime_type,
            'size': actual_size,
            'content_type': actual_content_type,
        })
        
        logger.info(f"Downloaded to cache: {file_id} → {actual_size} bytes ({filename})")
        return cache_path
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout downloading {file_id}")
        _cleanup_partial(cache_path)
        return None
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error downloading {file_id}: {e}")
        _cleanup_partial(cache_path)
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error downloading {file_id}: {e}")
        _cleanup_partial(cache_path)
        return None
    except Exception as e:
        logger.error(f"Unexpected error downloading {file_id}: {e}")
        _cleanup_partial(cache_path)
        return None
    finally:
        session.close()


def _cleanup_partial(cache_path: str):
    """Remove partial download file"""
    try:
        if os.path.exists(cache_path):
            os.remove(cache_path)
    except OSError:
        pass


# ============================================================================
# File Info (without API Key)
# ============================================================================

def get_gdrive_file_info(file_id: str) -> Optional[Dict[str, Any]]:
    """
    Get basic file info by doing a HEAD-like request.
    Returns: dict with filename, mime_type, size
    """
    # Check cache metadata first
    cached_meta = get_cached_meta(file_id)
    if cached_meta:
        return {
            'filename': cached_meta.get('filename', ''),
            'mime_type': cached_meta.get('mime_type', ''),
            'size': cached_meta.get('size', 0),
        }
    
    session = requests.Session()
    session.headers.update({'User-Agent': USER_AGENT})
    
    try:
        url = GDRIVE_DOWNLOAD_URL.format(file_id=file_id)
        response = session.get(url, stream=True, timeout=15)
        
        content_type = response.headers.get('Content-Type', '')
        size = int(response.headers.get('Content-Length', 0))
        
        filename = ''
        cd = response.headers.get('Content-Disposition', '')
        if cd:
            fname_match = re.search(r"filename\*?=['\"]?(?:UTF-8'')?([^'\";\n]+)", cd)
            if fname_match:
                filename = fname_match.group(1).strip()
        
        response.close()
        
        return {
            'filename': filename,
            'mime_type': content_type,
            'size': size,
        }
    except Exception as e:
        logger.error(f"Failed to get file info for {file_id}: {e}")
        return None
    finally:
        session.close()


# ============================================================================
# Admin Helper
# ============================================================================

def import_from_gdrive_url(url: str) -> Dict[str, Any]:
    """
    Import media info from Google Drive URL.
    Returns dict with metadata for creating StreamMedia.
    """
    file_id = extract_file_id(url)
    if not file_id:
        return {'error': 'Could not extract file ID from URL'}
    
    info = get_gdrive_file_info(file_id)
    if not info:
        return {'error': f'Could not get file info for ID: {file_id}'}
    
    mime_type = info.get('mime_type', '')
    if 'video' in mime_type:
        media_type = 'video'
    elif 'audio' in mime_type:
        media_type = 'audio'
    else:
        media_type = 'video'
    
    title = info.get('filename', 'Untitled')
    if title:
        title = os.path.splitext(title)[0]
        title = title.replace('_', ' ').replace('-', ' ')
    
    return {
        'file_id': file_id,
        'title': title or 'Untitled',
        'metadata': {
            'media_type': media_type,
            'mime_type': mime_type,
            'file_size': info.get('size', 0),
        }
    }
