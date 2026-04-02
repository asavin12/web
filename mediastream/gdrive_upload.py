"""
Google Drive Upload Service — Upload media lên Google Drive qua Service Account.

Yêu cầu:
  1. Service Account JSON credentials (lưu trong SiteConfiguration.gdrive_service_account_json)
  2. Một thư mục trên Google Drive được share với Service Account (root folder)
  3. Hệ thống tự động phát hiện root folder, tạo subfolder Video/Audio/Podcast

Luồng:
  1. Auto-detect root folder (thư mục được share với SA)
  2. Tạo subfolder nếu chưa có
  3. Upload file vào đúng subfolder theo media type
  4. Lưu mapping vào SiteConfiguration.gdrive_folder_mapping
"""

import json
import logging
from io import BytesIO

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/drive']

# Subfolder names created automatically on GDrive per media type
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
    """Check if a folder still exists and is accessible on GDrive."""
    try:
        f = service.files().get(fileId=folder_id, fields='id,trashed').execute()
        return not f.get('trashed', False)
    except Exception:
        return False


def _find_root_folder(service):
    """
    Auto-detect the root folder shared with the Service Account.
    Looks for the top-level folder that contains subfolders or is the main shared folder.
    Returns: (folder_id, folder_name) or (None, None)
    """
    try:
        # List ALL accessible folders
        result = service.files().list(
            q="mimeType='application/vnd.google-apps.folder' and trashed=false",
            pageSize=100,
            fields='files(id,name,parents)',
            orderBy='name',
        ).execute()
        folders = result.get('files', [])
        if not folders:
            return None, None

        # Build set of all folder IDs
        all_ids = {f['id'] for f in folders}

        # Find folders whose parent is NOT in our accessible set → these are top-level
        top_level = []
        for f in folders:
            parents = f.get('parents', [])
            if not parents or not any(p in all_ids for p in parents):
                top_level.append(f)

        if not top_level:
            # Fallback: use first folder
            top_level = folders[:1]

        # If there's exactly one top-level folder, that's the root
        if len(top_level) == 1:
            return top_level[0]['id'], top_level[0]['name']

        # Multiple top-level folders: pick the one that is NOT a media-type name
        media_names = {n.lower() for n in MEDIA_TYPE_FOLDER_NAMES.values()}
        media_names.update(MEDIA_TYPE_FOLDER_NAMES.keys())

        for f in top_level:
            if f['name'].lower() not in media_names:
                return f['id'], f['name']

        # All top-level are media-type names → no clear root
        return None, None

    except Exception as e:
        logger.error(f"Error finding root folder: {e}")
        return None, None


def _find_subfolder(service, parent_id, name):
    """Find a subfolder by name inside parent. Case-insensitive search."""
    for search_name in [name, name.lower(), name.capitalize()]:
        query = (
            "mimeType='application/vnd.google-apps.folder' and trashed=false"
            f" and name='{search_name}'"
        )
        if parent_id:
            query += f" and '{parent_id}' in parents"
        try:
            result = service.files().list(
                q=query, pageSize=1, fields='files(id,name)',
            ).execute()
            if result.get('files'):
                return result['files'][0]['id'], result['files'][0]['name']
        except Exception:
            pass
    return None, None


def _ensure_root_folder(service):
    """
    Ensure we have a valid root folder. Auto-detect if not configured or stale.
    Updates SiteConfiguration.gdrive_folder_id if changed.
    Returns root_folder_id or None.
    """
    from core.models import SiteConfiguration
    config = SiteConfiguration.get_instance()
    current_root = config.gdrive_folder_id or None

    # Check if current root is valid
    if current_root and _folder_exists(service, current_root):
        return current_root

    # Auto-detect root folder
    root_id, root_name = _find_root_folder(service)
    if root_id:
        logger.info(f"Auto-detected root GDrive folder: '{root_name}' (id={root_id})")
        config.gdrive_folder_id = root_id
        config.save(update_fields=['gdrive_folder_id'])
        return root_id

    logger.warning("No root GDrive folder found")
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
    1. Check cached mapping — verify folder still exists
    2. If stale, search inside root folder
    3. If not found, create subfolder in root
    4. Save updated mapping

    Returns: folder_id or None
    """
    from core.models import SiteConfiguration
    config = SiteConfiguration.get_instance()

    sa_dict, _ = _get_gdrive_config()
    if not sa_dict:
        return None

    mapping = config.gdrive_folder_mapping or {}
    service = _build_drive_service(sa_dict)

    # Check cached mapping
    cached_id = mapping.get(media_type)
    if cached_id and _folder_exists(service, cached_id):
        return cached_id

    # Ensure root folder
    root_id = _ensure_root_folder(service)

    # Search for subfolder inside root
    folder_name = MEDIA_TYPE_FOLDER_NAMES.get(media_type, media_type.capitalize())
    folder_id, _ = _find_subfolder(service, root_id, folder_name)

    if not folder_id:
        # Create subfolder in root
        folder_id = _create_gdrive_folder(service, folder_name, root_id)

    # Update mapping
    mapping[media_type] = folder_id
    _save_mapping(mapping)
    return folder_id


def ensure_all_media_folders():
    """
    Ensure all media type folders exist on GDrive.
    ALWAYS verifies on GDrive directly — never trusts cache.
    Auto-detects root folder, creates missing subfolders.
    Returns: {media_type: {id, name, created}} or {error: str}
    """
    sa_dict, _ = _get_gdrive_config()
    if not sa_dict:
        return {'error': 'GDrive chưa cấu hình Service Account'}

    try:
        service = _build_drive_service(sa_dict)

        # Ensure root folder exists
        root_id = _ensure_root_folder(service)
        if not root_id:
            return {'error': 'Không tìm thấy thư mục gốc. Hãy share thư mục với Service Account.'}

        results = {}
        fresh_mapping = {}

        for media_type, folder_name in MEDIA_TYPE_FOLDER_NAMES.items():
            # Search inside root folder
            folder_id, found_name = _find_subfolder(service, root_id, folder_name)

            if folder_id:
                results[media_type] = {'id': folder_id, 'name': found_name, 'created': False}
            else:
                folder_id = _create_gdrive_folder(service, folder_name, root_id)
                results[media_type] = {'id': folder_id, 'name': folder_name, 'created': True}

            fresh_mapping[media_type] = folder_id

        # Overwrite mapping
        _save_mapping(fresh_mapping)

        # Get root info for response
        from core.models import SiteConfiguration
        config = SiteConfiguration.get_instance()
        try:
            root_info = service.files().get(fileId=root_id, fields='id,name').execute()
            results['_root'] = {'id': root_id, 'name': root_info.get('name', '')}
        except Exception:
            results['_root'] = {'id': root_id, 'name': ''}

        return results

    except Exception as e:
        logger.error(f"Error ensuring GDrive folders: {e}")
        return {'error': str(e)[:300]}


def check_gdrive_connection(sa_json_str=None):
    """
    Test Google Drive connection. Auto-detects root folder.
    Updates gdrive_folder_id and gdrive_folder_mapping with verified data.
    
    Returns: {
        'connected': bool,
        'email': str,
        'root_folder': {id, name} | None,
        'folder_name': str,
        'folder_accessible': bool,
        'subfolders': [{id, name, media_type}],
        'visible_folders': [{id, name}],
        'error': str | None,
    }
    """
    result = {
        'connected': False,
        'email': '',
        'folder_name': '',
        'folder_accessible': False,
        'root_folder': None,
        'subfolders': [],
        'visible_folders': [],
        'error': None,
    }

    try:
        if sa_json_str:
            sa_dict = json.loads(sa_json_str)
        else:
            sa_dict, _ = _get_gdrive_config()

        if not sa_dict:
            result['error'] = 'Service Account JSON chưa được cấu hình'
            return result

        result['email'] = sa_dict.get('client_email', '')
        service = _build_drive_service(sa_dict)

        # Test credentials
        service.files().list(pageSize=1, fields='files(id)').execute()
        result['connected'] = True

        # Auto-detect root folder
        root_id = _ensure_root_folder(service)

        if root_id:
            try:
                root_info = service.files().get(fileId=root_id, fields='id,name').execute()
                result['root_folder'] = {'id': root_id, 'name': root_info.get('name', '')}
                result['folder_name'] = root_info.get('name', '')
                result['folder_accessible'] = True
            except Exception:
                result['root_folder'] = {'id': root_id, 'name': ''}
                result['folder_accessible'] = False

            # Find subfolders inside root
            fresh_mapping = {}
            subfolders = []
            for media_type, folder_name in MEDIA_TYPE_FOLDER_NAMES.items():
                fid, fname = _find_subfolder(service, root_id, folder_name)
                if fid:
                    subfolders.append({'id': fid, 'name': fname, 'media_type': media_type})
                    fresh_mapping[media_type] = fid
            result['subfolders'] = subfolders

            # Update mapping with verified data
            _save_mapping(fresh_mapping)

            # Also update folder_id back into result for legacy API compatibility
            from core.models import SiteConfiguration
            config = SiteConfiguration.get_instance()
            result['folder_id'] = config.gdrive_folder_id or ''
        else:
            result['folder_accessible'] = False
            result['error'] = (
                'Không tìm thấy thư mục gốc. Hãy share một thư mục với email: '
                f'{result["email"]} (quyền Editor)'
            )

        # List all visible folders for info
        try:
            visible = service.files().list(
                q="mimeType='application/vnd.google-apps.folder' and trashed=false",
                pageSize=50,
                fields='files(id,name)',
                orderBy='name',
            ).execute()
            result['visible_folders'] = [
                {'id': f['id'], 'name': f['name']}
                for f in visible.get('files', [])
            ]
        except Exception:
            pass

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

