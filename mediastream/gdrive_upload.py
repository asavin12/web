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

SCOPES = ['https://www.googleapis.com/auth/drive.file']


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


def list_gdrive_folders(parent_folder_id=None):
    """
    List folders inside a parent folder (or root if None).
    Returns: list of {id, name}
    """
    sa_dict, default_folder_id = _get_gdrive_config()
    if not sa_dict:
        return []

    target_folder = parent_folder_id or default_folder_id

    try:
        service = _build_drive_service(sa_dict)

        query = "mimeType='application/vnd.google-apps.folder' and trashed=false"
        if target_folder:
            query += f" and '{target_folder}' in parents"

        results = service.files().list(
            q=query,
            pageSize=50,
            fields='files(id,name)',
            orderBy='name',
        ).execute()

        return [{'id': f['id'], 'name': f['name']} for f in results.get('files', [])]
    except Exception as e:
        logger.error(f"Error listing GDrive folders: {e}")
        return []


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


def create_gdrive_folder(folder_name, parent_folder_id=None):
    """Create a new folder on Google Drive."""
    sa_dict, default_folder_id = _get_gdrive_config()
    if not sa_dict:
        return None

    target_parent = parent_folder_id or default_folder_id

    try:
        service = _build_drive_service(sa_dict)

        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
        }
        if target_parent:
            file_metadata['parents'] = [target_parent]

        folder = service.files().create(
            body=file_metadata,
            fields='id,name',
        ).execute()

        return {'id': folder['id'], 'name': folder['name']}
    except Exception as e:
        logger.error(f"Error creating GDrive folder: {e}")
        return None
