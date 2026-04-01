"""
Google Drive Upload Service — Upload video lên Google Drive qua Service Account.

Yêu cầu:
  1. Service Account JSON credentials (lưu trong SiteConfiguration.gdrive_service_account_json)
  2. Folder ID trên Google Drive (lưu trong SiteConfiguration.gdrive_folder_id)
  3. Folder phải được share với email của Service Account (Edit permission)

Luồng:
  User upload video → Server → Google Drive API → shareable link → lưu vào StreamMedia
"""

import json
import logging
from io import BytesIO

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/drive']

# Folder names created automatically on GDrive per media type
MEDIA_TYPE_FOLDER_NAMES = {
    'video': 'Video',
    'audio': 'Audio',
    'podcast': 'Podcast',
}


def _get_gdrive_config():
    """Get Google Drive config from SiteConfiguration. Returns (sa_json_dict, folder_id) or (None, None)."""
    try:
        from core.models import SiteConfiguration
        config = SiteConfiguration.get_instance()
        sa_json = config.gdrive_service_account_json
        folder_id = config.gdrive_folder_id
        if not sa_json:
            return None, None
        sa_dict = json.loads(sa_json)
        return sa_dict, folder_id or None
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Error loading GDrive config: {e}")
        return None, None


def _build_drive_service(sa_dict):
    """Build Google Drive API service from service account dict."""
    credentials = service_account.Credentials.from_service_account_info(
        sa_dict, scopes=SCOPES
    )
    return build('drive', 'v3', credentials=credentials, cache_discovery=False)


def _create_gdrive_folder(service, name, parent_folder_id=None):
    """Create a folder on Google Drive. Returns folder ID."""
    metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
    }
    if parent_folder_id:
        metadata['parents'] = [parent_folder_id]
    folder = service.files().create(body=metadata, fields='id,name').execute()
    logger.info(f"Created GDrive folder '{name}' (id={folder['id']})")
    return folder['id']


def _folder_exists(service, folder_id):
    """Check if a folder still exists on GDrive (not trashed). Returns True/False."""
    try:
        f = service.files().get(fileId=folder_id, fields='id,trashed').execute()
        return not f.get('trashed', False)
    except Exception:
        return False


def _find_accessible_folder(service, name):
    """
    Search ALL accessible folders (globally) for a folder with the given name.
    Returns folder ID or None.
    """
    query = (
        "mimeType='application/vnd.google-apps.folder' and trashed=false"
        f" and name='{name}'"
    )
    try:
        result = service.files().list(
            q=query, pageSize=1, fields='files(id,name)',
        ).execute()
        files = result.get('files', [])
        return files[0]['id'] if files else None
    except Exception:
        return None


def _save_mapping(mapping):
    """Save folder mapping to SiteConfiguration."""
    from core.models import SiteConfiguration
    config = SiteConfiguration.get_instance()
    config.gdrive_folder_mapping = mapping
    config.save(update_fields=['gdrive_folder_mapping'])


def get_folder_for_media_type(media_type):
    """
    Get the GDrive folder ID for a specific media type.
    1. Check cached mapping — VERIFY folder still exists on GDrive
    2. If stale/missing, search all accessible folders globally
    3. If not found, create new folder
    4. Save updated mapping

    Returns: folder_id or None (if GDrive not configured)
    """
    from core.models import SiteConfiguration
    config = SiteConfiguration.get_instance()

    sa_dict, root_folder_id = _get_gdrive_config()
    if not sa_dict:
        return None

    mapping = config.gdrive_folder_mapping or {}
    service = _build_drive_service(sa_dict)

    # Check cached mapping — verify it's still alive on GDrive
    cached_id = mapping.get(media_type)
    if cached_id and _folder_exists(service, cached_id):
        return cached_id

    # Cache miss or stale — search GDrive globally
    folder_name = MEDIA_TYPE_FOLDER_NAMES.get(media_type, media_type.capitalize())
    folder_id = None
    for search_name in [media_type, folder_name]:
        folder_id = _find_accessible_folder(service, search_name)
        if folder_id:
            logger.info(f"Found existing GDrive folder '{search_name}' (id={folder_id})")
            break

    if not folder_id:
        folder_id = _create_gdrive_folder(service, folder_name, root_folder_id)

    # Update mapping
    mapping[media_type] = folder_id
    _save_mapping(mapping)
    return folder_id


def ensure_all_media_folders():
    """
    Ensure all media type folders exist on GDrive.
    ALWAYS verifies on GDrive — never trusts cached mapping.
    Overwrites mapping with fresh verified data.
    Returns: {media_type: {id, name, created}} mapping
    """
    sa_dict, root_folder_id = _get_gdrive_config()
    if not sa_dict:
        return {'error': 'GDrive chưa cấu hình Service Account'}

    results = {}
    fresh_mapping = {}

    try:
        service = _build_drive_service(sa_dict)

        for media_type, folder_name in MEDIA_TYPE_FOLDER_NAMES.items():
            # Always search GDrive fresh — ignore cached mapping
            found_id = None
            found_name = None
            for search_name in [media_type, folder_name]:
                found_id = _find_accessible_folder(service, search_name)
                if found_id:
                    found_name = search_name
                    break

            if found_id:
                results[media_type] = {'id': found_id, 'name': found_name, 'created': False}
            else:
                found_id = _create_gdrive_folder(service, folder_name, root_folder_id)
                results[media_type] = {'id': found_id, 'name': folder_name, 'created': True}

            fresh_mapping[media_type] = found_id

        # Overwrite mapping with fresh verified data
        _save_mapping(fresh_mapping)
        return results

    except Exception as e:
        logger.error(f"Error ensuring GDrive folders: {e}")
        return {'error': str(e)[:300]}


def check_gdrive_connection(sa_json_str=None):
    """
    Test Google Drive connection with service account credentials.
    
    Returns: {
        'connected': bool,
        'email': str,        # Service account email
        'folder_name': str,  # Target folder name (if folder_id configured)
        'folder_accessible': bool,
        'error': str | None,
    }
    """
    result = {
        'connected': False,
        'email': '',
        'folder_name': '',
        'folder_accessible': False,
        'error': None,
    }

    try:
        # Use provided JSON or load from config
        if sa_json_str:
            sa_dict = json.loads(sa_json_str)
            from core.models import SiteConfiguration
            config = SiteConfiguration.get_instance()
            folder_id = config.gdrive_folder_id or None
        else:
            sa_dict, folder_id = _get_gdrive_config()

        if not sa_dict:
            result['error'] = 'Service Account JSON chưa được cấu hình'
            return result

        result['email'] = sa_dict.get('client_email', '')

        # Build service and test
        service = _build_drive_service(sa_dict)

        # Test: list files (limit 1) to verify credentials work
        service.files().list(pageSize=1, fields='files(id)').execute()
        result['connected'] = True

        # Check folder access if configured
        if folder_id:
            try:
                folder = service.files().get(
                    fileId=folder_id, fields='id,name,mimeType'
                ).execute()
                if folder.get('mimeType') == 'application/vnd.google-apps.folder':
                    result['folder_name'] = folder.get('name', '')
                    result['folder_accessible'] = True
                else:
                    result['error'] = f'ID "{folder_id}" không phải folder'
            except Exception as e:
                result['folder_accessible'] = False
                err = str(e)
                if '404' in err or 'not found' in err.lower() or 'notFound' in err:
                    result['error'] = (
                        f'Folder "{folder_id}" không tìm thấy. '
                        f'Hãy chia sẻ (Share) thư mục với email: {result["email"]} (quyền Editor)'
                    )
                elif '403' in err or 'forbidden' in err.lower():
                    result['error'] = (
                        f'Không có quyền truy cập folder. '
                        f'Hãy Share thư mục với {result["email"]} (quyền Editor)'
                    )
                else:
                    result['error'] = f'Không truy cập được folder: {err[:200]}'

        # List visible folders — only actual existing non-trashed folders
        # Also update folder_mapping with verified data
        try:
            visible = service.files().list(
                q="mimeType='application/vnd.google-apps.folder' and trashed=false",
                pageSize=50,
                fields='files(id,name)',
                orderBy='name',
            ).execute()
            all_folders = visible.get('files', [])

            # Deduplicate by name (case-insensitive), keep first occurrence
            seen_names = set()
            unique_folders = []
            for f in all_folders:
                key = f['name'].lower()
                if key not in seen_names:
                    seen_names.add(key)
                    unique_folders.append({'id': f['id'], 'name': f['name']})
            result['visible_folders'] = unique_folders

            # Auto-update folder_mapping with real verified folder IDs
            fresh_mapping = {}
            for media_type, expected_name in MEDIA_TYPE_FOLDER_NAMES.items():
                # Search for folder by media_type key ('video') or display name ('Video')
                for f in all_folders:
                    if f['name'].lower() == media_type or f['name'] == expected_name:
                        fresh_mapping[media_type] = f['id']
                        break
            if fresh_mapping:
                _save_mapping(fresh_mapping)

        except Exception:
            result['visible_folders'] = []

    except json.JSONDecodeError:
        result['error'] = 'Service Account JSON không hợp lệ'
    except Exception as e:
        error_msg = str(e)
        if 'invalid_grant' in error_msg.lower():
            result['error'] = 'Service Account credentials không hợp lệ hoặc đã hết hạn'
        elif 'access_denied' in error_msg.lower() or '403' in error_msg:
            result['error'] = 'Service Account không có quyền truy cập Google Drive API'
        else:
            result['error'] = f'Lỗi kết nối: {error_msg[:300]}'

    return result



def upload_to_gdrive(file_obj, filename, mime_type='video/mp4', folder_id=None):
    """
    Upload a file to Google Drive.
    
    Args:
        file_obj: Django UploadedFile or file-like object with read()
        filename: Target filename on Google Drive
        mime_type: MIME type of the file
        folder_id: Target folder ID (uses default from config if None)
    
    Returns: {
        'success': bool,
        'file_id': str,
        'gdrive_url': str,    # Shareable link
        'web_view_link': str,  # Google Drive viewer link
        'error': str | None,
    }
    """
    sa_dict, default_folder_id = _get_gdrive_config()
    if not sa_dict:
        return {'success': False, 'error': 'Service Account JSON chưa được cấu hình'}

    target_folder = folder_id or default_folder_id

    try:
        service = _build_drive_service(sa_dict)

        # File metadata
        file_metadata = {'name': filename}
        if target_folder:
            file_metadata['parents'] = [target_folder]

        # Read file into BytesIO for the API
        if hasattr(file_obj, 'read'):
            content = file_obj.read()
            if hasattr(file_obj, 'seek'):
                file_obj.seek(0)
        else:
            content = file_obj

        media_body = MediaIoBaseUpload(
            BytesIO(content),
            mimetype=mime_type,
            resumable=True,
            chunksize=5 * 1024 * 1024,  # 5MB chunks
        )

        # Upload
        uploaded = service.files().create(
            body=file_metadata,
            media_body=media_body,
            fields='id,name,webViewLink,webContentLink',
        ).execute()

        file_id = uploaded['id']

        # Set file to "Anyone with link can view"
        service.permissions().create(
            fileId=file_id,
            body={'type': 'anyone', 'role': 'reader'},
        ).execute()

        gdrive_url = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
        web_view_link = uploaded.get('webViewLink', gdrive_url)

        return {
            'success': True,
            'file_id': file_id,
            'gdrive_url': gdrive_url,
            'web_view_link': web_view_link,
            'error': None,
        }

    except Exception as e:
        logger.error(f"GDrive upload error: {e}", exc_info=True)
        return {'success': False, 'error': f'Upload thất bại: {str(e)[:300]}'}

