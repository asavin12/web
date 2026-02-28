"""
Media Scanner — Scan for unused media files in the project.

Compares physical files in MEDIA_ROOT against all DB references:
  - All FileField / ImageField values across all models
  - Inline <img src="/media/..."> references in HTML content fields
  - cover_image_srcset JSON fields

Returns a list of files that exist on disk but are NOT referenced anywhere.
"""

import os
import re
from pathlib import Path

from django.conf import settings
from django.apps import apps


# Fields that may contain HTML with inline image references
CONTENT_FIELDS = [
    ('news', 'Article', 'content'),
    ('knowledge', 'Article', 'content'),
    ('tools', 'Tool', 'description'),
    ('tools', 'Tool', 'embed_code'),
    ('resources', 'Resource', 'description'),
]

# JSON fields that store srcset media paths
SRCSET_FIELDS = [
    ('news', 'Article', 'cover_image_srcset'),
    ('knowledge', 'Article', 'cover_image_srcset'),
    ('tools', 'Tool', 'cover_image_srcset'),
]

# Directories to skip (not user-uploaded content)
SKIP_DIRS = {
    'logos',           # Site logos (managed separately)
    'gdrive_cache',    # Google Drive cache (auto-generated)
    '.thumbnails',     # Auto-generated thumbnails
}

# File extensions considered media
MEDIA_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.ico',
    '.mp4', '.webm', '.ogg', '.mov', '.avi', '.flv', '.m4v',
    '.mp3', '.wav', '.m4a', '.aac', '.flac', '.wma',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.zip', '.rar', '.7z', '.tar', '.gz',
    '.vtt', '.srt',
}


def get_all_physical_files():
    """
    Walk MEDIA_ROOT and collect all physical files.
    Returns dict: {relative_path: {size, mtime, abs_path}}
    """
    media_root = str(settings.MEDIA_ROOT)
    files = {}

    for dirpath, dirnames, filenames in os.walk(media_root):
        # Skip excluded directories
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for filename in filenames:
            abs_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(abs_path, media_root)

            # Only include known media extensions
            ext = os.path.splitext(filename)[1].lower()
            if ext not in MEDIA_EXTENSIONS:
                continue

            try:
                stat = os.stat(abs_path)
                files[rel_path] = {
                    'abs_path': abs_path,
                    'size': stat.st_size,
                    'mtime': stat.st_mtime,
                }
            except OSError:
                continue

    return files


def get_all_db_references():
    """
    Collect ALL media file references from the database.
    Scans: FileField, ImageField, content HTML, srcset JSON.
    Returns a set of relative paths (relative to MEDIA_ROOT).
    """
    referenced = set()

    # 1. Scan all FileField / ImageField values across ALL models
    for model in apps.get_models():
        file_fields = []
        for field in model._meta.get_fields():
            if hasattr(field, 'get_internal_type'):
                ftype = field.get_internal_type()
                if ftype in ('FileField', 'ImageField'):
                    file_fields.append(field.name)

        if not file_fields:
            continue

        try:
            qs = model.objects.only(*file_fields).iterator(chunk_size=500)
            for obj in qs:
                for fname in file_fields:
                    value = getattr(obj, fname, None)
                    if value and hasattr(value, 'name') and value.name:
                        referenced.add(value.name)
        except Exception:
            # Some models may have issues (proxy, unmanaged, etc.)
            continue

    # 2. Scan HTML content fields for inline <img src="/media/...">
    media_url = settings.MEDIA_URL  # e.g. /media/
    img_pattern = re.compile(
        r'(?:src|href)=["\']'
        + re.escape(media_url)
        + r'([^"\']+)["\']',
        re.IGNORECASE,
    )

    for app_label, model_name, field_name in CONTENT_FIELDS:
        try:
            model = apps.get_model(app_label, model_name)
            for obj in model.objects.only(field_name).iterator(chunk_size=200):
                content = getattr(obj, field_name, '') or ''
                for match in img_pattern.finditer(content):
                    referenced.add(match.group(1))
        except Exception:
            continue

    # 3. Scan srcset JSON fields
    for app_label, model_name, field_name in SRCSET_FIELDS:
        try:
            model = apps.get_model(app_label, model_name)
            for obj in model.objects.only(field_name).iterator(chunk_size=200):
                srcset_data = getattr(obj, field_name, None)
                if not srcset_data or not isinstance(srcset_data, dict):
                    continue
                for _key, url in srcset_data.items():
                    if isinstance(url, str) and url.startswith(media_url):
                        referenced.add(url[len(media_url):])
                    elif isinstance(url, str) and not url.startswith(('http://', 'https://')):
                        referenced.add(url)
        except Exception:
            continue

    return referenced


def scan_unused_media():
    """
    Main scanner: compare physical files vs DB references.
    Returns list of dicts: [{rel_path, abs_path, size, mtime, folder, filename}]
    sorted by folder then filename
    """
    physical = get_all_physical_files()
    referenced = get_all_db_references()

    # Normalize referenced paths (some may have leading slash or different separators)
    normalized_refs = set()
    for ref in referenced:
        # Remove leading slashes, normalize path separators
        clean = ref.lstrip('/').replace('\\', '/')
        normalized_refs.add(clean)

    unused = []
    for rel_path, info in physical.items():
        normalized = rel_path.replace('\\', '/')
        if normalized not in normalized_refs:
            parts = normalized.split('/')
            folder = parts[0] if len(parts) > 1 else '(root)'
            unused.append({
                'rel_path': normalized,
                'abs_path': info['abs_path'],
                'size': info['size'],
                'mtime': info['mtime'],
                'folder': folder,
                'filename': os.path.basename(normalized),
            })

    unused.sort(key=lambda x: (x['folder'], x['filename']))
    return unused


def delete_media_files(rel_paths):
    """
    Permanently delete specified media files from disk.
    Returns (deleted_count, errors).
    """
    media_root = str(settings.MEDIA_ROOT)
    deleted = 0
    errors = []

    for rel_path in rel_paths:
        abs_path = os.path.normpath(os.path.join(media_root, rel_path))
        # Safety: ensure path is within MEDIA_ROOT
        if not abs_path.startswith(media_root):
            errors.append(f'Path escape attempt: {rel_path}')
            continue
        try:
            if os.path.isfile(abs_path):
                os.remove(abs_path)
                deleted += 1
            else:
                errors.append(f'Not found: {rel_path}')
        except OSError as e:
            errors.append(f'{rel_path}: {e}')

    return deleted, errors
