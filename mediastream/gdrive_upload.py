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


def _resolve_root_folder(service, config_folder_id):
    """
    Resolve the actual root folder. If gdrive_folder_id itself is a
    media-type folder (e.g. named 'video'), go up to its parent so that
    Video/Audio/Podcast are siblings, not children.
    Returns the correct root folder ID (may update SiteConfiguration).
    """
    if not config_folder_id:
        return None

    try:
        info = service.files().get(
            fileId=config_folder_id, fields='id,name,parents'
        ).execute()
        folder_name = info.get('name', '').strip().lower()

        # Check if this folder IS a media-type folder
        media_type_names = {n.lower() for n in MEDIA_TYPE_FOLDER_NAMES.values()}
        media_type_names.update(MEDIA_TYPE_FOLDER_NAMES.keys())  # also check keys like 'video'

        if folder_name in media_type_names and info.get('parents'):
            parent_id = info['parents'][0]
            logger.info(
                f"gdrive_folder_id points to media-type folder '{info['name']}' "
                f"(id={config_folder_id}). Updating root to parent (id={parent_id})."
            )
            # Update config to use the parent as root
            from core.models import SiteConfiguration
            cfg = SiteConfiguration.get_instance()
            cfg.gdrive_folder_id = parent_id
            cfg.save(update_fields=['gdrive_folder_id'])
            return parent_id
    except Exception as e:
        logger.warning(f"Could not resolve root folder: {e}")

    return config_folder_id


def get_folder_for_media_type(media_type):
    """
    Get the GDrive folder ID for a specific media type.
    Auto-creates the folder inside the root GDrive folder if it doesn't exist yet.
    Updates SiteConfiguration.gdrive_folder_mapping automatically.

    Returns: folder_id or None (if GDrive not configured)
    """
    from core.models import SiteConfiguration
    config = SiteConfiguration.get_instance()

    sa_dict, root_folder_id = _get_gdrive_config()
    if not sa_dict:
        return None

    mapping = config.gdrive_folder_mapping or {}

    # Check if already mapped
    folder_id = mapping.get(media_type)
    if folder_id:
        return folder_id

    # Auto-create: build service, create subfolder in root
    folder_name = MEDIA_TYPE_FOLDER_NAMES.get(media_type, media_type.capitalize())
    try:
        service = _build_drive_service(sa_dict)

        # Auto-fix: if root is itself a media-type folder, go up to parent
        root_folder_id = _resolve_root_folder(service, root_folder_id)

        # Search for existing folder (both 'Video' and 'video')
        folder_id = None
        for search_name in [folder_name, media_type]:
            query = (
                "mimeType='application/vnd.google-apps.folder' and trashed=false"
                f" and name='{search_name}'"
            )
            if root_folder_id:
                query += f" and '{root_folder_id}' in parents"

            existing = service.files().list(
                q=query, pageSize=1, fields='files(id,name)',
            ).execute()

            if existing.get('files'):
                folder_id = existing['files'][0]['id']
                logger.info(f"Found existing GDrive folder '{search_name}' (id={folder_id})")
                break

        if not folder_id:
            folder_id = _create_gdrive_folder(service, folder_name, root_folder_id)

        # Save mapping
        mapping[media_type] = folder_id
        config.gdrive_folder_mapping = mapping
        config.save(update_fields=['gdrive_folder_mapping'])

        return folder_id

    except Exception as e:
        logger.error(f"Error getting/creating GDrive folder for '{media_type}': {e}")
        return root_folder_id  # Fallback to root


def ensure_all_media_folders():
    """
    Ensure all media type folders exist on GDrive.
    Called from admin or management command.
    Returns: {media_type: {id, name, created}} mapping
    """
    from core.models import SiteConfiguration
    config = SiteConfiguration.get_instance()

    sa_dict, root_folder_id = _get_gdrive_config()
    if not sa_dict:
        return {'error': 'GDrive chưa cấu hình Service Account'}

    mapping = config.gdrive_folder_mapping or {}
    results = {}

    try:
        service = _build_drive_service(sa_dict)

        # Auto-fix: if root is itself a media-type folder, go up to parent
        root_folder_id = _resolve_root_folder(service, root_folder_id)

        # Clear mapping so we re-discover at correct level
        mapping = {}

        for media_type, folder_name in MEDIA_TYPE_FOLDER_NAMES.items():

            # Search for existing folder by name (both 'Video' and 'video')
            found_id = None
            for search_name in [folder_name, media_type]:
                query = (
                    "mimeType='application/vnd.google-apps.folder' and trashed=false"
                    f" and name='{search_name}'"
                )
                if root_folder_id:
                    query += f" and '{root_folder_id}' in parents"

                found = service.files().list(
                    q=query, pageSize=1, fields='files(id,name)',
                ).execute()

                if found.get('files'):
                    found_id = found['files'][0]['id']
                    results[media_type] = {'id': found_id, 'name': found['files'][0]['name'], 'created': False}
                    break

            if not found_id:
                found_id = _create_gdrive_folder(service, folder_name, root_folder_id)
                results[media_type] = {'id': found_id, 'name': folder_name, 'created': True}

            mapping[media_type] = found_id

        # Save all at once
        config.gdrive_folder_mapping = mapping
        config.save(update_fields=['gdrive_folder_mapping'])

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

        # List visible folders for debugging
        try:
            visible = service.files().list(
                q="mimeType='application/vnd.google-apps.folder' and trashed=false",
                pageSize=10,
                fields='files(id,name)',
                orderBy='modifiedTime desc',
            ).execute()
            result['visible_folders'] = [
                {'id': f['id'], 'name': f['name']}
                for f in visible.get('files', [])
            ]
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

