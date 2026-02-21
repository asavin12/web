"""
MinIO/S3 Storage Configuration cho MediaStream
Sử dụng django-storages với boto3 để upload/stream từ MinIO trên Coolify
Đọc config từ Admin Panel (SiteSettings) hoặc environment variables
"""

from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings


def get_minio_config():
    """
    Lấy MinIO config từ database (SiteSettings) hoặc env
    Ưu tiên database > env variables > defaults
    """
    try:
        from core.models import SiteSettings
        config = SiteSettings.get_minio_config()
        if config:
            return config
    except Exception:
        pass
    
    # Fallback to env/settings
    endpoint = getattr(settings, 'MINIO_ENDPOINT_URL', None)
    if not endpoint:
        return None
        
    return {
        'endpoint_url': endpoint,
        'access_key': getattr(settings, 'MINIO_ACCESS_KEY', ''),
        'secret_key': getattr(settings, 'MINIO_SECRET_KEY', ''),
        'bucket': getattr(settings, 'MINIO_MEDIA_BUCKET', 'mediastream'),
        'region': getattr(settings, 'MINIO_REGION', 'us-east-1'),
        'custom_domain': getattr(settings, 'MINIO_CUSTOM_DOMAIN', None),
    }


class MediaStreamStorage(S3Boto3Storage):
    """
    Custom storage backend cho MediaStream
    Kết nối với MinIO trên Coolify
    Đọc config từ Admin Panel
    """
    
    def __init__(self, **settings_override):
        # Get config from database/env
        config = get_minio_config() or {}
        
        # Set attributes from config
        self.bucket_name = config.get('bucket', 'mediastream')
        self.endpoint_url = config.get('endpoint_url')
        self.access_key = config.get('access_key')
        self.secret_key = config.get('secret_key')
        self.custom_domain = config.get('custom_domain')
        self.region_name = config.get('region', 'us-east-1')
        
        # File settings
        self.file_overwrite = False  # Không ghi đè file cùng tên
        self.default_acl = 'private'  # Private by default
        self.signature_version = 's3v4'
        
        super().__init__(**settings_override)
    
    def get_object_parameters(self, name):
        """
        Set Content-Type và Cache-Control cho từng loại file
        """
        params = {}
        
        # Detect content type
        name_lower = name.lower()
        
        # Video files
        if name_lower.endswith('.mp4'):
            params['ContentType'] = 'video/mp4'
        elif name_lower.endswith('.webm'):
            params['ContentType'] = 'video/webm'
        elif name_lower.endswith('.ogg') or name_lower.endswith('.ogv'):
            params['ContentType'] = 'video/ogg'
        elif name_lower.endswith('.avi'):
            params['ContentType'] = 'video/x-msvideo'
        elif name_lower.endswith('.mov'):
            params['ContentType'] = 'video/quicktime'
        elif name_lower.endswith('.flv'):
            params['ContentType'] = 'video/x-flv'
        
        # Audio files
        elif name_lower.endswith('.mp3'):
            params['ContentType'] = 'audio/mpeg'
        elif name_lower.endswith('.wav'):
            params['ContentType'] = 'audio/wav'
        elif name_lower.endswith('.flac'):
            params['ContentType'] = 'audio/flac'
        elif name_lower.endswith('.aac'):
            params['ContentType'] = 'audio/aac'
        elif name_lower.endswith('.m4a'):
            params['ContentType'] = 'audio/mp4'
        
        # Subtitle files
        elif name_lower.endswith('.vtt'):
            params['ContentType'] = 'text/vtt'
        elif name_lower.endswith('.srt'):
            params['ContentType'] = 'text/plain'
        
        # Image files
        elif name_lower.endswith('.jpg') or name_lower.endswith('.jpeg'):
            params['ContentType'] = 'image/jpeg'
        elif name_lower.endswith('.png'):
            params['ContentType'] = 'image/png'
        elif name_lower.endswith('.webp'):
            params['ContentType'] = 'image/webp'
        elif name_lower.endswith('.gif'):
            params['ContentType'] = 'image/gif'
        
        # Cache control
        params['CacheControl'] = 'public, max-age=31536000'  # 1 year
        
        return params


class PublicMediaStreamStorage(MediaStreamStorage):
    """
    Storage cho public media (thumbnails, etc.)
    Files có thể được truy cập trực tiếp qua MinIO URL
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.default_acl = 'public-read'
        self.querystring_auth = False


class PrivateMediaStreamStorage(MediaStreamStorage):
    """
    Storage cho private media (video/audio files)
    Files được serve qua Django với referrer protection
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.default_acl = 'private'
        self.querystring_auth = True
        self.querystring_expire = 3600  # URL hết hạn sau 1 giờ
    
    def url(self, name, parameters=None, expire=None, http_method=None):
        """
        Generate signed URL cho private files
        """
        if expire is None:
            expire = self.querystring_expire
        
        return super().url(name, parameters=parameters, expire=expire, http_method=http_method)


def is_minio_configured():
    """Kiểm tra xem MinIO đã được cấu hình chưa"""
    config = get_minio_config()
    return config is not None and config.get('endpoint_url')


def get_media_storage():
    """
    Factory function để lấy storage backend phù hợp
    Kiểm tra MinIO config từ database hoặc env
    """
    if is_minio_configured():
        return PrivateMediaStreamStorage()
    else:
        # Fallback về FileSystemStorage
        from django.core.files.storage import FileSystemStorage
        return FileSystemStorage(location=settings.MEDIA_ROOT)


def get_thumbnail_storage():
    """
    Factory function cho thumbnail storage
    """
    if is_minio_configured():
        return PublicMediaStreamStorage()
    else:
        from django.core.files.storage import FileSystemStorage
        return FileSystemStorage(location=settings.MEDIA_ROOT)
