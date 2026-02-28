"""
File Manager Views - Admin file management
"""

import os
import json
import shutil
from pathlib import Path

from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from django.core.files.storage import default_storage
from django.contrib import messages

from core.image_utils import convert_to_webp, should_convert_to_webp


def get_safe_path(relative_path, base_path):
    """Ensure path is within base_path (prevent directory traversal)"""
    # Convert PosixPath to string if needed
    base_path = str(base_path)
    
    if not relative_path:
        return base_path
    
    full_path = os.path.normpath(os.path.join(base_path, relative_path))
    if not full_path.startswith(base_path):
        return base_path
    return full_path


def get_file_info(file_path, base_url):
    """Get file/folder information"""
    name = os.path.basename(file_path)
    is_dir = os.path.isdir(file_path)
    
    info = {
        'name': name,
        'path': file_path,
        'is_dir': is_dir,
        'is_image': False,
        'size': 0,
        'size_display': '-',
        'url': None,
    }
    
    if not is_dir:
        size = os.path.getsize(file_path)
        info['size'] = size
        
        if size < 1024:
            info['size_display'] = f"{size} B"
        elif size < 1024 * 1024:
            info['size_display'] = f"{size / 1024:.1f} KB"
        else:
            info['size_display'] = f"{size / (1024 * 1024):.1f} MB"
        
        # Check if image
        ext = os.path.splitext(name)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']:
            info['is_image'] = True
        
        # Generate URL
        relative_to_media = os.path.relpath(file_path, str(settings.MEDIA_ROOT))
        info['url'] = f"{settings.MEDIA_URL}{relative_to_media}"
    
    return info


@staff_member_required
def file_browser(request):
    """Browse files in media directory"""
    current_path = request.GET.get('path', '')
    media_root = str(settings.MEDIA_ROOT)
    
    full_path = get_safe_path(current_path, media_root)
    
    items = []
    if os.path.isdir(full_path):
        for name in os.listdir(full_path):
            item_path = os.path.join(full_path, name)
            item_info = get_file_info(item_path, settings.MEDIA_URL)
            item_info['relative_path'] = os.path.join(current_path, name) if current_path else name
            items.append(item_info)
    
    # Sort: folders first, then files alphabetically
    items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
    
    # Breadcrumb
    breadcrumbs = []
    if current_path:
        parts = current_path.split(os.sep)
        for i, part in enumerate(parts):
            breadcrumbs.append({
                'name': part,
                'path': os.sep.join(parts[:i+1])
            })
    
    context = {
        'items': items,
        'current_path': current_path,
        'parent_path': os.path.dirname(current_path) if current_path else None,
        'breadcrumbs': breadcrumbs,
        'media_url': settings.MEDIA_URL,
    }
    
    return render(request, 'admin/filemanager/file_browser.html', context)


@staff_member_required
@require_http_methods(["POST"])
@csrf_protect
def upload_file(request):
    """Upload file(s) to media directory with auto WebP conversion and unstressvn- prefix"""
    current_path = request.POST.get('path', '')
    files = request.FILES.getlist('files')
    convert_webp = request.POST.get('convert_webp', 'true') == 'true'
    custom_slug = request.POST.get('slug', '')  # Optional custom slug for naming
    
    media_root = str(settings.MEDIA_ROOT)
    upload_dir = get_safe_path(current_path, media_root)
    
    if not os.path.isdir(upload_dir):
        return JsonResponse({'error': 'Invalid upload directory'}, status=400)
    
    uploaded = []
    for f in files:
        # Convert to WebP if image
        if convert_webp and should_convert_to_webp(f.name):
            webp_content = convert_to_webp(f, quality='high', slug=custom_slug or None)
            if webp_content:
                file_path = os.path.join(upload_dir, webp_content.name)
                with open(file_path, 'wb') as dest:
                    dest.write(webp_content.read())
                uploaded.append(webp_content.name)
                continue
        
        # Save original file (non-image or conversion disabled)
        # Still add unstressvn prefix for non-image files
        from core.image_utils import generate_image_filename, sanitize_filename
        original_ext = os.path.splitext(f.name)[1]
        if custom_slug:
            new_name = f"unstressvn-{sanitize_filename(custom_slug)}{original_ext}"
        else:
            new_name = f"unstressvn-{sanitize_filename(f.name)}"
        
        file_path = os.path.join(upload_dir, new_name)
        with open(file_path, 'wb') as dest:
            for chunk in f.chunks():
                dest.write(chunk)
        uploaded.append(new_name)
    
    return JsonResponse({
        'success': True,
        'uploaded': uploaded,
        'count': len(uploaded)
    })


@staff_member_required
@require_http_methods(["POST"])
@csrf_protect
def create_folder(request):
    """Create new folder"""
    current_path = request.POST.get('path', '')
    folder_name = request.POST.get('name', '').strip()
    
    if not folder_name:
        return JsonResponse({'error': 'Folder name is required'}, status=400)
    
    # Sanitize folder name
    folder_name = "".join(c for c in folder_name if c.isalnum() or c in (' ', '-', '_')).strip()
    if not folder_name:
        return JsonResponse({'error': 'Invalid folder name'}, status=400)
    
    media_root = str(settings.MEDIA_ROOT)
    parent_dir = get_safe_path(current_path, media_root)
    new_folder = os.path.join(parent_dir, folder_name)
    
    if os.path.exists(new_folder):
        return JsonResponse({'error': 'Folder already exists'}, status=400)
    
    try:
        os.makedirs(new_folder)
        return JsonResponse({'success': True, 'folder': folder_name})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
@require_http_methods(["POST"])
@csrf_protect
def delete_item(request):
    """Delete file or folder"""
    item_path = request.POST.get('path', '')
    
    if not item_path:
        return JsonResponse({'error': 'Path is required'}, status=400)
    
    media_root = str(settings.MEDIA_ROOT)
    full_path = get_safe_path(item_path, media_root)
    
    # Prevent deleting media root
    if full_path == media_root:
        return JsonResponse({'error': 'Cannot delete media root'}, status=400)
    
    if not os.path.exists(full_path):
        return JsonResponse({'error': 'Item not found'}, status=404)
    
    try:
        if os.path.isdir(full_path):
            shutil.rmtree(full_path)
        else:
            os.remove(full_path)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
@require_http_methods(["POST"])
@csrf_protect
def rename_item(request):
    """Rename file or folder"""
    item_path = request.POST.get('path', '')
    new_name = request.POST.get('name', '').strip()
    
    if not item_path or not new_name:
        return JsonResponse({'error': 'Path and name are required'}, status=400)
    
    # Sanitize new name
    new_name = "".join(c for c in new_name if c.isalnum() or c in (' ', '-', '_', '.')).strip()
    
    media_root = str(settings.MEDIA_ROOT)
    full_path = get_safe_path(item_path, media_root)
    
    if not os.path.exists(full_path):
        return JsonResponse({'error': 'Item not found'}, status=404)
    
    parent_dir = os.path.dirname(full_path)
    new_path = os.path.join(parent_dir, new_name)
    
    if os.path.exists(new_path):
        return JsonResponse({'error': 'Item with this name already exists'}, status=400)
    
    try:
        os.rename(full_path, new_path)
        return JsonResponse({'success': True, 'new_name': new_name})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required  
def disk_usage(request):
    """Get disk usage statistics with detailed breakdown"""
    media_root = str(settings.MEDIA_ROOT)
    
    # Overall stats
    total_size = 0
    file_count = 0
    folder_count = 0
    
    # Stats by folder
    folder_stats = {}
    
    # Stats by file type
    type_stats = {
        'images': {'extensions': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.ico'], 'size': 0, 'count': 0},
        'videos': {'extensions': ['.mp4', '.webm', '.ogg', '.avi', '.mov', '.flv', '.m4v'], 'size': 0, 'count': 0},
        'audio': {'extensions': ['.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a', '.wma'], 'size': 0, 'count': 0},
        'documents': {'extensions': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt'], 'size': 0, 'count': 0},
        'other': {'extensions': [], 'size': 0, 'count': 0},
    }
    
    for root, dirs, files in os.walk(media_root):
        folder_count += len(dirs)
        
        # Get relative folder path
        rel_folder = os.path.relpath(root, media_root)
        if rel_folder == '.':
            rel_folder = 'root'
        else:
            # Get top-level folder
            rel_folder = rel_folder.split(os.sep)[0]
        
        for f in files:
            file_path = os.path.join(root, f)
            try:
                file_size = os.path.getsize(file_path)
            except OSError:
                continue
                
            file_count += 1
            total_size += file_size
            
            # Add to folder stats
            if rel_folder not in folder_stats:
                folder_stats[rel_folder] = {'size': 0, 'count': 0}
            folder_stats[rel_folder]['size'] += file_size
            folder_stats[rel_folder]['count'] += 1
            
            # Add to type stats
            ext = os.path.splitext(f)[1].lower()
            categorized = False
            for type_name, type_info in type_stats.items():
                if ext in type_info['extensions']:
                    type_info['size'] += file_size
                    type_info['count'] += 1
                    categorized = True
                    break
            if not categorized:
                type_stats['other']['size'] += file_size
                type_stats['other']['count'] += 1
    
    def format_size(size):
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"
    
    # Format folder stats
    folder_list = []
    for name, stats in sorted(folder_stats.items(), key=lambda x: x[1]['size'], reverse=True):
        folder_list.append({
            'name': name,
            'size': stats['size'],
            'size_display': format_size(stats['size']),
            'count': stats['count'],
            'percentage': (stats['size'] / total_size * 100) if total_size > 0 else 0
        })
    
    # Format type stats
    type_list = []
    type_icons = {
        'images': '🖼️',
        'videos': '🎬',
        'audio': '🎵',
        'documents': '📄',
        'other': '📁'
    }
    type_colors = {
        'images': '#4CAF50',
        'videos': '#2196F3',
        'audio': '#9C27B0',
        'documents': '#FF9800',
        'other': '#607D8B'
    }
    for type_name, type_info in type_stats.items():
        if type_info['count'] > 0:
            type_list.append({
                'name': type_name.capitalize(),
                'icon': type_icons.get(type_name, '📁'),
                'color': type_colors.get(type_name, '#999'),
                'size': type_info['size'],
                'size_display': format_size(type_info['size']),
                'count': type_info['count'],
                'percentage': (type_info['size'] / total_size * 100) if total_size > 0 else 0
            })
    type_list.sort(key=lambda x: x['size'], reverse=True)
    
    # Check MinIO storage
    minio_info = None
    try:
        from core.models import SiteConfiguration
        minio_config = SiteConfiguration.get_instance().get_minio_config()
        if minio_config and minio_config.get('endpoint_url'):
            import boto3
            from botocore.config import Config
            
            s3_client = boto3.client(
                's3',
                endpoint_url=minio_config['endpoint_url'],
                aws_access_key_id=minio_config['access_key'],
                aws_secret_access_key=minio_config['secret_key'],
                region_name=minio_config.get('region', 'us-east-1'),
                config=Config(signature_version='s3v4', connect_timeout=5, read_timeout=5)
            )
            
            bucket = minio_config.get('bucket', 'mediastream')
            minio_size = 0
            minio_count = 0
            
            try:
                paginator = s3_client.get_paginator('list_objects_v2')
                for page in paginator.paginate(Bucket=bucket):
                    for obj in page.get('Contents', []):
                        minio_size += obj.get('Size', 0)
                        minio_count += 1
                
                minio_info = {
                    'endpoint': minio_config['endpoint_url'],
                    'bucket': bucket,
                    'size': minio_size,
                    'size_display': format_size(minio_size),
                    'count': minio_count,
                    'status': 'connected'
                }
            except Exception as e:
                minio_info = {
                    'endpoint': minio_config['endpoint_url'],
                    'bucket': bucket,
                    'status': 'error',
                    'error': str(e)[:100]
                }
    except Exception:
        pass
    
    # Check if JSON response requested
    if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
        return JsonResponse({
            'total_size': total_size,
            'size_display': format_size(total_size),
            'file_count': file_count,
            'folder_count': folder_count,
            'folders': folder_list,
            'types': type_list,
            'minio': minio_info
        })
    
    # Render template
    context = {
        'title': 'Disk Usage - Storage Overview',
        'total_size': total_size,
        'size_display': format_size(total_size),
        'file_count': file_count,
        'folder_count': folder_count,
        'folders': folder_list,
        'types': type_list,
        'minio': minio_info,
    }
    
    return render(request, 'admin/filemanager/disk_usage.html', context)


# ═══════════════════════════════════════════
# Unused Media Scanner
# ═══════════════════════════════════════════

@staff_member_required
@csrf_protect
def unused_media(request):
    """
    Scan and display unused media files.
    GET  — run scan, show results
    POST — delete selected files
    """
    from .media_scanner import scan_unused_media, delete_media_files

    if request.method == 'POST':
        selected = request.POST.getlist('selected_files')
        if selected:
            deleted, errors = delete_media_files(selected)
            if deleted:
                messages.success(request, f'✅ Đã xoá {deleted} file không sử dụng.')
            for err in errors:
                messages.error(request, f'❌ {err}')
        else:
            messages.warning(request, '⚠️ Chưa chọn file nào.')
        return redirect('filemanager:unused_media')

    # GET — scan
    unused = scan_unused_media()
    total_size = sum(f['size'] for f in unused)

    # Pre-compute display sizes
    for f in unused:
        f['size_display'] = _format_size(f['size'])

    # Group by folder
    folders = {}
    for f in unused:
        folder = f['folder']
        if folder not in folders:
            folders[folder] = {'files': [], 'size': 0, 'count': 0}
        folders[folder]['files'].append(f)
        folders[folder]['size'] += f['size']
        folders[folder]['count'] += 1

    for data in folders.values():
        data['size_display'] = _format_size(data['size'])

    context = {
        'title': 'Quét Media Không Sử Dụng',
        'unused_files': unused,
        'total_count': len(unused),
        'total_size': total_size,
        'total_size_display': _format_size(total_size),
        'folders': dict(sorted(folders.items())),
    }
    return render(request, 'admin/filemanager/unused_media.html', context)


def _format_size(size_bytes):
    """Format bytes to human-readable size"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

