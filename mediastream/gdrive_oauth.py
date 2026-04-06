"""
Google Drive OAuth2 Multi-Account System.

Cho phép thêm nhiều tài khoản Gmail miễn phí (15GB mỗi tài khoản).
Upload file vào tài khoản có nhiều dung lượng trống nhất.

OAuth2 Flow:
  1. Admin clicks "Thêm tài khoản Gmail"
  2. Redirect → Google consent screen
  3. User authorizes → callback saves refresh_token
  4. Upload sử dụng refresh_token để lấy access_token
"""

import json
import logging
import os
import urllib.parse
from datetime import timedelta

import requests
from django.utils import timezone

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/userinfo.email',
]

# Subfolder names
MEDIA_TYPE_FOLDER_NAMES = {
    'video': 'Video',
    'audio': 'Audio',
    'podcast': 'Podcast',
}

ROOT_FOLDER_NAME = 'UnstressVN'


def _get_oauth_config():
    """Get OAuth2 client_id and client_secret from SiteConfiguration."""
    from core.models import SiteConfiguration
    config = SiteConfiguration.get_instance()
    client_id = (config.gdrive_oauth_client_id or '').strip()
    client_secret = (config.gdrive_oauth_client_secret or '').strip()
    if not client_id or not client_secret:
        return None, None
    return client_id, client_secret


def get_authorize_url(redirect_uri):
    """Generate Google OAuth2 authorization URL."""
    client_id, _ = _get_oauth_config()
    if not client_id:
        return None

    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': ' '.join(SCOPES),
        'access_type': 'offline',
        'prompt': 'consent',  # Force to always return refresh_token
    }
    return f'{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}'


def exchange_code_for_tokens(code, redirect_uri):
    """Exchange authorization code for access_token + refresh_token."""
    client_id, client_secret = _get_oauth_config()
    if not client_id:
        return None, 'OAuth2 chưa cấu hình Client ID/Secret'

    resp = requests.post(GOOGLE_TOKEN_URL, data={
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
    }, timeout=30)

    if resp.status_code != 200:
        logger.error('OAuth2 token exchange failed: %s', resp.text)
        return None, f'Google trả lỗi: {resp.json().get("error_description", resp.text)}'

    data = resp.json()
    refresh_token = data.get('refresh_token')
    access_token = data.get('access_token')

    if not refresh_token:
        return None, 'Không nhận được refresh_token. Thử xóa quyền app trong Google Account Settings rồi thử lại.'

    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_in': data.get('expires_in', 3600),
    }, None


def _build_credentials(account):
    """Build Google OAuth2 Credentials from a GDriveAccount."""
    client_id, client_secret = _get_oauth_config()
    if not client_id:
        return None

    return Credentials(
        token=None,
        refresh_token=account.refresh_token,
        token_uri=GOOGLE_TOKEN_URL,
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )


def build_drive_service(account):
    """Build Google Drive API service from a GDriveAccount."""
    creds = _build_credentials(account)
    if not creds:
        return None
    return build('drive', 'v3', credentials=creds, cache_discovery=False)


def get_account_email(access_token):
    """Get Gmail email from access token via userinfo or Drive API."""
    # Try userinfo endpoint first
    try:
        resp = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10,
        )
        if resp.status_code == 200:
            email = resp.json().get('email', '')
            if email:
                return email
    except Exception:
        pass

    # Fallback: get email from Drive API about endpoint
    try:
        resp = requests.get(
            'https://www.googleapis.com/drive/v3/about?fields=user',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get('user', {}).get('emailAddress', '')
    except Exception:
        pass

    return ''


def update_storage_info(account):
    """Fetch and update storage usage for a GDriveAccount."""
    try:
        service = build_drive_service(account)
        if not service:
            return False
        about = service.about().get(fields='storageQuota,user').execute()
        quota = about.get('storageQuota', {})
        account.storage_used = int(quota.get('usage', 0))
        account.storage_total = int(quota.get('limit', 15 * 1024**3))
        account.last_storage_check = timezone.now()
        account.save(update_fields=['storage_used', 'storage_total', 'last_storage_check'])
        return True
    except Exception as e:
        logger.error('Failed to update storage for %s: %s', account.email, e)
        return False


def check_token_status(account):
    """
    Check if account's refresh_token is still valid.
    Returns dict: {valid: bool, error: str|None}
    """
    try:
        creds = _build_credentials(account)
        if not creds:
            return {'valid': False, 'error': 'Không thể tạo credentials (thiếu OAuth2 config)'}
        # Force a token refresh
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        return {'valid': True, 'error': None}
    except Exception as e:
        err_msg = str(e)
        if 'invalid_grant' in err_msg.lower() or 'token' in err_msg.lower():
            return {'valid': False, 'error': 'Token hết hạn hoặc bị thu hồi — cần cấp phép lại'}
        return {'valid': False, 'error': err_msg[:200]}


def select_best_account(min_free_bytes=0):
    """
    Select the GDrive account with most free space.
    Returns GDriveAccount or None.
    """
    from .models import GDriveAccount
    accounts = GDriveAccount.objects.filter(is_active=True).order_by('storage_used')

    best = None
    best_free = -1
    for acc in accounts:
        free = acc.storage_free
        if free > best_free and free >= min_free_bytes:
            best = acc
            best_free = free

    return best


def _ensure_folder(service, name, parent_id=None):
    """Find or create a folder. Returns folder_id."""
    q = f"mimeType='application/vnd.google-apps.folder' and trashed=false and name='{name}'"
    if parent_id:
        q += f" and '{parent_id}' in parents"

    result = service.files().list(q=q, pageSize=1, fields='files(id)').execute()
    files = result.get('files', [])
    if files:
        return files[0]['id']

    metadata = {'name': name, 'mimeType': 'application/vnd.google-apps.folder'}
    if parent_id:
        metadata['parents'] = [parent_id]
    folder = service.files().create(body=metadata, fields='id').execute()
    logger.info("Created GDrive folder '%s' (id=%s)", name, folder['id'])
    return folder['id']


def ensure_account_folders(account):
    """
    Ensure root + media type folders exist for an account.
    Creates 'UnstressVN/Video', 'UnstressVN/Audio', 'UnstressVN/Podcast'.
    Updates account.root_folder_id and account.folder_mapping.
    """
    try:
        service = build_drive_service(account)
        if not service:
            return False

        # Ensure root folder
        root_id = account.root_folder_id
        if root_id:
            try:
                service.files().get(fileId=root_id, fields='id,trashed').execute()
            except Exception:
                root_id = ''

        if not root_id:
            root_id = _ensure_folder(service, ROOT_FOLDER_NAME)
            account.root_folder_id = root_id

        # Ensure media type subfolders
        mapping = {}
        for media_type, folder_name in MEDIA_TYPE_FOLDER_NAMES.items():
            folder_id = _ensure_folder(service, folder_name, root_id)
            mapping[media_type] = folder_id

        account.folder_mapping = mapping
        account.save(update_fields=['root_folder_id', 'folder_mapping'])
        return True
    except Exception as e:
        logger.error('Failed to ensure folders for %s: %s', account.email, e)
        return False


def get_folder_for_upload(account, media_type):
    """Get folder ID for a media type on a specific account."""
    mapping = account.folder_mapping or {}
    folder_id = mapping.get(media_type)
    if folder_id:
        return folder_id

    # Try to create folders
    ensure_account_folders(account)
    mapping = account.folder_mapping or {}
    return mapping.get(media_type)


def upload_to_account(account, file_obj, filename, mime_type='video/mp4', media_type='video'):
    """
    Upload a file to a specific GDrive account.

    Returns: {
        'success': bool,
        'file_id': str,
        'gdrive_url': str,
        'account_email': str,
        'error': str | None,
    }
    """
    try:
        service = build_drive_service(account)
        if not service:
            return {'success': False, 'error': f'Không thể kết nối {account.email}'}

        # Get target folder
        folder_id = get_folder_for_upload(account, media_type)

        file_metadata = {'name': filename}
        if folder_id:
            file_metadata['parents'] = [folder_id]

        # Prepare file
        if hasattr(file_obj, 'file'):
            fd = file_obj.file
        elif hasattr(file_obj, 'read'):
            fd = file_obj
        else:
            from io import BytesIO
            fd = BytesIO(file_obj)
        fd.seek(0)

        media_body = MediaIoBaseUpload(
            fd,
            mimetype=mime_type,
            resumable=True,
            chunksize=10 * 1024 * 1024,
        )

        uploaded = service.files().create(
            body=file_metadata,
            media_body=media_body,
            fields='id,name,webViewLink,webContentLink',
        ).execute()

        file_id = uploaded['id']

        # Set public sharing
        service.permissions().create(
            fileId=file_id,
            body={'type': 'anyone', 'role': 'reader'},
        ).execute()

        # Update account metadata
        account.last_used = timezone.now()
        account.storage_used += file_obj.size if hasattr(file_obj, 'size') else 0
        account.save(update_fields=['last_used', 'storage_used'])

        gdrive_url = f'https://drive.google.com/file/d/{file_id}/view?usp=sharing'

        return {
            'success': True,
            'file_id': file_id,
            'gdrive_url': gdrive_url,
            'web_view_link': uploaded.get('webViewLink', gdrive_url),
            'account_email': account.email,
            'error': None,
        }

    except Exception as e:
        logger.error('Upload to %s failed: %s', account.email, e, exc_info=True)
        return {
            'success': False,
            'error': f'Upload lên {account.email} thất bại: {str(e)[:300]}',
        }


def fetch_gdrive_file_metadata(file_id):
    """
    Lấy metadata video từ Google Drive (duration, size, resolution, thumbnail).
    
    Chiến lược 3 tầng:
    1. Drive API: files().get() → videoMediaMetadata (nhanh nhất)
    2. ffprobe: probe trực tiếp URL download → duration, resolution
    3. Kết hợp: nếu API có size nhưng thiếu duration → ffprobe bổ sung
    
    Returns:
        Dict với keys: name, size, mime_type, duration_seconds, width, height, thumbnail_path
        Hoặc None nếu không lấy được.
    """
    from .models import GDriveAccount
    
    accounts = list(GDriveAccount.objects.filter(is_active=True))
    if not accounts:
        logger.warning("Không có GDrive account active nào để fetch metadata")
        return None
    
    result = None
    download_url = None
    
    # Tier 1: Google Drive API
    for account in accounts:
        try:
            service = build_drive_service(account)
            if not service:
                continue
            
            file_info = service.files().get(
                fileId=file_id,
                fields='id,name,size,mimeType,videoMediaMetadata,webContentLink',
                supportsAllDrives=True,
            ).execute()
            
            result = {
                'name': file_info.get('name', ''),
                'size': int(file_info.get('size', 0)),
                'mime_type': file_info.get('mimeType', ''),
            }
            
            # Video metadata (Google Drive auto-processes uploaded videos)
            video_meta = file_info.get('videoMediaMetadata', {})
            if video_meta:
                duration_ms = video_meta.get('durationMillis')
                if duration_ms:
                    result['duration_seconds'] = int(int(duration_ms) / 1000)
                if video_meta.get('width'):
                    result['width'] = video_meta['width']
                if video_meta.get('height'):
                    result['height'] = video_meta['height']
            
            # Get authenticated download URL for ffprobe fallback
            download_url, access_token = _get_authenticated_download_url(service, account, file_id)
            
            logger.info(
                "GDrive API OK cho %s: name=%s, size=%s, duration=%s, has_video_meta=%s",
                file_id, result['name'], result['size'],
                result.get('duration_seconds', 'N/A'),
                bool(video_meta)
            )
            break  # Got file info from API
            
        except Exception as e:
            logger.warning("GDrive API fetch via %s failed for %s: %s", account.email, file_id, e)
            continue
    
    if not result:
        logger.warning("Không lấy được metadata GDrive cho file %s", file_id)
        return None
    
    # Tier 2: ffprobe fallback nếu thiếu duration
    if not result.get('duration_seconds') and download_url:
        logger.info("GDrive API thiếu duration cho %s, dùng ffprobe...", file_id)
        probe_info = _ffprobe_url(download_url, access_token=access_token)
        if probe_info:
            if probe_info.get('duration'):
                result['duration_seconds'] = probe_info['duration']
            if probe_info.get('width') and not result.get('width'):
                result['width'] = probe_info['width']
            if probe_info.get('height') and not result.get('height'):
                result['height'] = probe_info['height']
    
    return result


def fetch_gdrive_metadata_batch(file_ids):
    """
    Batch fetch metadata cho nhiều Google Drive files.
    
    Returns:
        Dict mapping file_id → metadata dict.
    """
    from .models import GDriveAccount
    
    if not file_ids:
        return {}
    
    accounts = list(GDriveAccount.objects.filter(is_active=True))
    if not accounts:
        logger.warning("Không có GDrive account active nào")
        return {}
    
    results = {}
    download_urls = {}
    fields = 'id,name,size,mimeType,videoMediaMetadata,webContentLink'
    
    # Tier 1: Google Drive API for all files
    for account in accounts:
        service = build_drive_service(account)
        if not service:
            continue
        
        remaining_ids = [fid for fid in file_ids if fid not in results]
        for file_id in remaining_ids:
            try:
                file_info = service.files().get(
                    fileId=file_id,
                    fields=fields,
                    supportsAllDrives=True,
                ).execute()
                
                result = {
                    'name': file_info.get('name', ''),
                    'size': int(file_info.get('size', 0)),
                    'mime_type': file_info.get('mimeType', ''),
                }
                
                video_meta = file_info.get('videoMediaMetadata', {})
                if video_meta:
                    duration_ms = video_meta.get('durationMillis')
                    if duration_ms:
                        result['duration_seconds'] = int(int(duration_ms) / 1000)
                    if video_meta.get('width'):
                        result['width'] = video_meta['width']
                    if video_meta.get('height'):
                        result['height'] = video_meta['height']
                
                results[file_id] = result
                
                # Save download URL for ffprobe fallback
                if not result.get('duration_seconds'):
                    url, token = _get_authenticated_download_url(service, account, file_id)
                    if url:
                        download_urls[file_id] = (url, token)
                
                logger.info("GDrive batch: %s → %s (dur=%ss)", file_id, result['name'], result.get('duration_seconds', 'N/A'))
                
            except Exception as e:
                logger.warning("GDrive batch: %s failed via %s: %s", file_id, account.email, e)
                continue
        
        if len(results) == len(file_ids):
            break
    
    # Tier 2: ffprobe fallback cho files thiếu duration
    for file_id, (url, token) in download_urls.items():
        if file_id in results and not results[file_id].get('duration_seconds'):
            logger.info("ffprobe fallback cho %s...", file_id)
            probe_info = _ffprobe_url(url, access_token=token)
            if probe_info:
                if probe_info.get('duration'):
                    results[file_id]['duration_seconds'] = probe_info['duration']
                if probe_info.get('width') and not results[file_id].get('width'):
                    results[file_id]['width'] = probe_info['width']
                if probe_info.get('height') and not results[file_id].get('height'):
                    results[file_id]['height'] = probe_info['height']
    
    logger.info("GDrive batch: %d/%d files fetched", len(results), len(file_ids))
    return results


def _get_authenticated_download_url(service, account, file_id):
    """
    Lấy URL download + access_token từ Google Drive API.
    Returns: (url, access_token) tuple hoặc (None, None).
    """
    try:
        creds = _build_credentials(account)
        if not creds:
            return None, None
        if not creds.valid or creds.expired:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
        
        url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
        return url, creds.token
    except Exception as e:
        logger.debug("Failed to get auth download URL: %s", e)
        return None, None


def _ffprobe_url(url, access_token=None, timeout=45):
    """
    Dùng ffprobe để lấy duration + resolution từ URL.
    ffprobe chỉ đọc header/moov atom → không download toàn bộ file.
    
    Returns:
        Dict {duration: int, width: int, height: int} hoặc None
    """
    import subprocess
    import json as _json
    
    try:
        # Build headers: Authorization Bearer nếu có token
        headers_str = "User-Agent: Mozilla/5.0 (X11; Linux x86_64) Chrome/120.0\r\n"
        if access_token:
            headers_str = f"Authorization: Bearer {access_token}\r\n{headers_str}"
        
        cmd = [
            'ffprobe', '-v', 'error',
            '-print_format', 'json',
            '-show_format', '-show_streams',
            '-headers', headers_str,
            url,
        ]
        proc = subprocess.run(cmd, capture_output=True, timeout=timeout, text=True)
        
        if proc.returncode != 0:
            logger.warning("ffprobe failed (rc=%d): stderr=%s", proc.returncode, proc.stderr[:500] if proc.stderr else '(empty)')
            return None
        
        probe = _json.loads(proc.stdout)
        result = {}
        
        # Duration from format
        duration_str = probe.get('format', {}).get('duration')
        if duration_str:
            result['duration'] = int(float(duration_str))
        
        # Width/height from video stream
        for stream in probe.get('streams', []):
            if stream.get('codec_type') == 'video':
                if stream.get('width'):
                    result['width'] = stream['width']
                if stream.get('height'):
                    result['height'] = stream['height']
                # Duration from stream if not in format
                if not result.get('duration') and stream.get('duration'):
                    result['duration'] = int(float(stream['duration']))
                break
        
        if result.get('duration'):
            logger.info("ffprobe OK: duration=%ds, %sx%s", result['duration'], result.get('width', '?'), result.get('height', '?'))
            return result
        
        logger.warning("ffprobe: no duration found in output (stdout=%s)", proc.stdout[:300] if proc.stdout else '(empty)')
        return None
        
    except subprocess.TimeoutExpired:
        logger.warning("ffprobe timeout (%ds) cho URL", timeout)
        return None
    except Exception as e:
        logger.warning("ffprobe error: %s", e)
        return None


def extract_gdrive_thumbnail(file_id, duration_seconds=None):
    """
    Trích xuất thumbnail random từ video Google Drive.
    
    Dùng ffmpeg để lấy 1 frame tại thời điểm random (hoặc 25% video).
    Sử dụng Authorization header để download qua Google Drive API.
    
    Returns:
        Path to thumbnail file (caller phải cleanup) hoặc None
    """
    import subprocess
    import tempfile
    import random
    
    from .models import GDriveAccount
    
    # Get authenticated download URL
    accounts = list(GDriveAccount.objects.filter(is_active=True))
    download_url = None
    access_token = None
    
    for account in accounts:
        try:
            service = build_drive_service(account)
            if service:
                download_url, access_token = _get_authenticated_download_url(service, account, file_id)
                if download_url:
                    break
        except Exception:
            continue
    
    if not download_url:
        # Fallback: public download URL (no auth header)
        download_url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t"
        access_token = None
    
    # Build headers
    headers_str = "User-Agent: Mozilla/5.0 (X11; Linux x86_64) Chrome/120.0\r\n"
    if access_token:
        headers_str = f"Authorization: Bearer {access_token}\r\n{headers_str}"
    
    # Chọn thời điểm random: 10%-80% video, hoặc 5s nếu không biết duration
    if duration_seconds and duration_seconds > 10:
        seek_time = random.randint(int(duration_seconds * 0.1), int(duration_seconds * 0.8))
    elif duration_seconds and duration_seconds > 2:
        seek_time = int(duration_seconds * 0.25)
    else:
        seek_time = 5
    
    thumb_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            thumb_path = tmp.name
        
        cmd = [
            'ffmpeg', '-y',
            '-headers', headers_str,
            '-ss', str(seek_time),
            '-i', download_url,
            '-frames:v', '1',
            '-q:v', '2',
            '-vf', 'scale=640:-2',
            thumb_path,
        ]
        
        result = subprocess.run(cmd, capture_output=True, timeout=60, text=True)
        
        if result.returncode != 0:
            logger.info("ffmpeg thumbnail retry at ss=1 cho %s: %s", file_id, result.stderr[:200] if result.stderr else '')
            # Retry at beginning
            cmd[cmd.index('-ss') + 1] = '1'
            result = subprocess.run(cmd, capture_output=True, timeout=60, text=True)
        
        if result.returncode == 0 and os.path.isfile(thumb_path) and os.path.getsize(thumb_path) > 0:
            logger.info("GDrive thumbnail OK cho %s (seek=%ds): %s", file_id, seek_time, thumb_path)
            return thumb_path
        
        logger.warning("ffmpeg thumbnail failed cho %s: %s", file_id, result.stderr[:500] if result.stderr else '(empty)')
        if thumb_path and os.path.isfile(thumb_path):
            os.unlink(thumb_path)
        return None
        
    except subprocess.TimeoutExpired:
        logger.warning("ffmpeg thumbnail timeout cho %s", file_id)
        if thumb_path and os.path.isfile(thumb_path):
            os.unlink(thumb_path)
        return None
    except Exception as e:
        logger.warning("ffmpeg thumbnail error cho %s: %s", file_id, e)
        return None
