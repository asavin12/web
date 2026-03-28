"""
Storage helpers cho MediaStream — uses Django default (local) storage.
"""

from django.conf import settings
from django.core.files.storage import FileSystemStorage


def is_minio_configured():
    """Always False — MinIO integration removed."""
    return False


def get_media_storage():
    """Return default file storage."""
    return FileSystemStorage(location=settings.MEDIA_ROOT)


def get_thumbnail_storage():
    """Return default file storage."""
    return FileSystemStorage(location=settings.MEDIA_ROOT)
