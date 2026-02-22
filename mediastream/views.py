"""
Media Stream Views
Streaming video/audio với bảo vệ referrer - chỉ cho phép từ domain unstressvn.com
"""

import os
import re
import mimetypes
from urllib.parse import urlparse

from django.http import (
    HttpResponse, 
    HttpResponseForbidden, 
    HttpResponseNotFound,
    FileResponse,
    StreamingHttpResponse,
    JsonResponse
)
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.files.storage import default_storage
from django.db.models import Q

from .models import StreamMedia, MediaCategory, MediaSubtitle, MediaPlaylist


# ============================================================================
# REFERRER PROTECTION CONFIGURATION
# ============================================================================

# Các domain được phép truy cập media stream
# Video links CHỈHOẠT ĐỘNG trên domain unstressvn.com
ALLOWED_DOMAINS = [
    'unstressvn.com',
    'www.unstressvn.com',
]

# Development domains (chỉ cho phép trong DEBUG mode)
DEV_DOMAINS = [
    'localhost',
    '127.0.0.1',
]

# Có cho phép direct access (không có referrer) hay không
# False = chặn direct access (bảo mật hơn)
ALLOW_DIRECT_ACCESS = False

# Có check referrer trong DEBUG mode không
CHECK_REFERRER_IN_DEBUG = False


def is_allowed_referrer(request):
    """
    Kiểm tra referrer có hợp lệ hay không
    Returns: (is_allowed, reason)
    """
    # Bypass trong DEBUG mode nếu được cấu hình
    if settings.DEBUG and not CHECK_REFERRER_IN_DEBUG:
        return True, "debug_mode"
    
    referer = request.META.get('HTTP_REFERER', '')
    
    # Không có referrer
    if not referer:
        if ALLOW_DIRECT_ACCESS:
            return True, "direct_access_allowed"
        return False, "no_referrer"
    
    try:
        parsed = urlparse(referer)
        domain = parsed.netloc.lower()
        
        # Remove port if present
        if ':' in domain:
            domain = domain.split(':')[0]
        
        # Combine allowed domains
        all_allowed = ALLOWED_DOMAINS.copy()
        if settings.DEBUG:
            all_allowed.extend(DEV_DOMAINS)
        
        # Check against allowed domains
        for allowed in all_allowed:
            if domain == allowed or domain.endswith('.' + allowed):
                return True, f"allowed_domain:{domain}"
        
        return False, f"forbidden_domain:{domain}"
    
    except Exception as e:
        return False, f"parse_error:{str(e)}"


def referrer_protected(view_func):
    """
    Decorator để bảo vệ view bằng referrer check
    """
    def wrapper(request, *args, **kwargs):
        is_allowed, reason = is_allowed_referrer(request)
        
        if not is_allowed:
            # Log for debugging
            if settings.DEBUG:
                print(f"[MediaStream] Blocked access: {reason}")
            
            return HttpResponseNotFound(
                "<h1>404 Not Found</h1><p>The requested resource was not found.</p>",
                content_type="text/html"
            )
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


# ============================================================================
# STREAMING VIEWS
# ============================================================================

def range_re_compile():
    """Compile regex for Range header parsing"""
    return re.compile(r'bytes=(\d+)-(\d*)')


RANGE_RE = range_re_compile()


class RangeFileWrapper:
    """File wrapper that supports HTTP Range requests for streaming"""
    
    def __init__(self, file_obj, chunk_size=8192, offset=0, length=None):
        self.file_obj = file_obj
        self.chunk_size = chunk_size
        self.offset = offset
        self.length = length
        self.file_obj.seek(offset)
    
    def __iter__(self):
        remaining = self.length
        while remaining is None or remaining > 0:
            chunk_size = self.chunk_size if remaining is None else min(remaining, self.chunk_size)
            data = self.file_obj.read(chunk_size)
            if not data:
                break
            if remaining is not None:
                remaining -= len(data)
            yield data
    
    def close(self):
        if hasattr(self.file_obj, 'close'):
            self.file_obj.close()


@referrer_protected
@require_GET
def stream_media(request, uid):
    """
    Stream media với hỗ trợ HTTP Range (cho seeking video/audio)
    Hỗ trợ cả local storage, MinIO/S3 và Google Drive
    URL: /media-stream/play/<uid>/
    """
    try:
        media = StreamMedia.objects.get(uid=uid, is_active=True)
    except StreamMedia.DoesNotExist:
        return HttpResponseNotFound("Media not found")
    
    # Check if requires login
    if media.requires_login and not request.user.is_authenticated:
        return HttpResponseForbidden("Login required to access this content")
    
    # Check if public
    if not media.is_public and not request.user.is_authenticated:
        return HttpResponseForbidden("This content is not public")
    
    # Google Drive storage
    if media.storage_type == 'gdrive' and media.gdrive_file_id:
        return stream_from_gdrive(request, media)
    
    # Check if using MinIO/S3 storage
    if media.file:
        storage = media.file.storage
        is_s3_storage = hasattr(storage, 'bucket_name')
        
        if is_s3_storage:
            return stream_from_minio(request, media)
        else:
            return stream_from_local(request, media)
    
    return HttpResponseNotFound("No file available for this media")


def stream_from_minio(request, media):
    """
    Stream media từ MinIO/S3
    Option 1: Redirect to signed URL (không an toàn cho referrer protection)
    Option 2: Proxy qua Django (an toàn hơn nhưng tốn bandwidth server)
    
    Chọn Option 2 để duy trì referrer protection
    """
    import boto3
    from botocore.config import Config
    
    storage = media.file.storage
    
    # Get S3 client
    s3_client = boto3.client(
        's3',
        endpoint_url=storage.endpoint_url,
        aws_access_key_id=storage.access_key,
        aws_secret_access_key=storage.secret_key,
        region_name=getattr(storage, 'region_name', 'us-east-1'),
        config=Config(signature_version='s3v4')
    )
    
    bucket_name = storage.bucket_name
    file_key = media.file.name
    
    try:
        # Get object metadata
        head_response = s3_client.head_object(Bucket=bucket_name, Key=file_key)
        file_size = head_response['ContentLength']
        content_type = head_response.get('ContentType', media.mime_type or 'application/octet-stream')
    except Exception as e:
        if settings.DEBUG:
            print(f"[MediaStream] MinIO error: {e}")
        return HttpResponseNotFound("File not found on storage")
    
    # Check for Range header
    range_header = request.META.get('HTTP_RANGE', '')
    
    if range_header:
        range_match = RANGE_RE.match(range_header)
        if range_match:
            first_byte = int(range_match.group(1))
            last_byte = int(range_match.group(2)) if range_match.group(2) else file_size - 1
            
            if first_byte >= file_size:
                return HttpResponse(status=416)
            
            length = last_byte - first_byte + 1
            
            # Get object with range
            range_str = f'bytes={first_byte}-{last_byte}'
            s3_response = s3_client.get_object(
                Bucket=bucket_name,
                Key=file_key,
                Range=range_str
            )
            
            response = StreamingHttpResponse(
                s3_response['Body'].iter_chunks(chunk_size=8192),
                status=206,
                content_type=content_type
            )
            response['Content-Length'] = length
            response['Content-Range'] = f'bytes {first_byte}-{last_byte}/{file_size}'
        else:
            # Invalid range, get full object
            s3_response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
            response = StreamingHttpResponse(
                s3_response['Body'].iter_chunks(chunk_size=8192),
                content_type=content_type
            )
            response['Content-Length'] = file_size
    else:
        # No range, get full object
        s3_response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        response = StreamingHttpResponse(
            s3_response['Body'].iter_chunks(chunk_size=8192),
            content_type=content_type
        )
        response['Content-Length'] = file_size
    
    # Common headers
    response['Accept-Ranges'] = 'bytes'
    response['Cache-Control'] = 'public, max-age=86400'
    
    # CORS headers
    origin = request.META.get('HTTP_ORIGIN', '')
    if origin:
        parsed_origin = urlparse(origin)
        origin_domain = parsed_origin.netloc.split(':')[0] if ':' in parsed_origin.netloc else parsed_origin.netloc
        if any(origin_domain == d or origin_domain.endswith('.' + d) for d in ALLOWED_DOMAINS):
            response['Access-Control-Allow-Origin'] = origin
    
    # Increment view count (only for initial request)
    if not range_header:
        media.increment_view()
    
    return response


def stream_from_local(request, media):
    """Stream media từ local filesystem"""
    try:
        file_path = media.file.path
        file_size = os.path.getsize(file_path)
    except (ValueError, FileNotFoundError):
        return HttpResponseNotFound("File not found on server")
    
    # Get content type
    content_type = media.mime_type or mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
    
    # Check for Range header (for streaming/seeking)
    range_header = request.META.get('HTTP_RANGE', '')
    
    if range_header:
        # Parse range header
        range_match = RANGE_RE.match(range_header)
        if range_match:
            first_byte = int(range_match.group(1))
            last_byte = int(range_match.group(2)) if range_match.group(2) else file_size - 1
            
            if first_byte >= file_size:
                return HttpResponse(status=416)  # Range Not Satisfiable
            
            length = last_byte - first_byte + 1
            
            # Open file and create response
            file_obj = open(file_path, 'rb')
            response = StreamingHttpResponse(
                RangeFileWrapper(file_obj, offset=first_byte, length=length),
                status=206,
                content_type=content_type
            )
            response['Content-Length'] = length
            response['Content-Range'] = f'bytes {first_byte}-{last_byte}/{file_size}'
        else:
            # Invalid range header, return full file
            response = FileResponse(open(file_path, 'rb'), content_type=content_type)
            response['Content-Length'] = file_size
    else:
        # No range header, return full file
        response = FileResponse(open(file_path, 'rb'), content_type=content_type)
        response['Content-Length'] = file_size
    
    # Common headers
    response['Accept-Ranges'] = 'bytes'
    response['Cache-Control'] = 'public, max-age=86400'  # Cache 1 day
    
    # CORS headers for embedding (only for allowed origins)
    origin = request.META.get('HTTP_ORIGIN', '')
    if origin:
        parsed_origin = urlparse(origin)
        origin_domain = parsed_origin.netloc.split(':')[0] if ':' in parsed_origin.netloc else parsed_origin.netloc
        if any(origin_domain == d or origin_domain.endswith('.' + d) for d in ALLOWED_DOMAINS):
            response['Access-Control-Allow-Origin'] = origin
    
    # Increment view count (only for initial request, not range requests)
    if not range_header:
        media.increment_view()
    
    return response


def stream_from_gdrive(request, media):
    """
    Stream media từ Google Drive qua local cache.
    
    Luồng:
    1. Check cache → nếu có, stream từ cache (giống local)
    2. Nếu chưa cache → download từ GDrive → cache → stream
    
    Hỗ trợ đầy đủ HTTP Range/206 cho video seeking.
    """
    from .gdrive import download_to_cache, get_cached_file_size, is_cached
    
    file_id = media.gdrive_file_id
    if not file_id:
        return HttpResponseNotFound("No Google Drive file ID")
    
    # Download to cache if not already cached
    cache_path = download_to_cache(file_id)
    if not cache_path:
        return HttpResponse("Failed to fetch from Google Drive", status=502)
    
    try:
        file_size = os.path.getsize(cache_path)
    except OSError:
        return HttpResponseNotFound("Cached file not found")
    
    # Get content type
    content_type = media.mime_type or mimetypes.guess_type(cache_path)[0] or 'application/octet-stream'
    
    # Check for Range header (for streaming/seeking)
    range_header = request.META.get('HTTP_RANGE', '')
    
    if range_header:
        range_match = RANGE_RE.match(range_header)
        if range_match:
            first_byte = int(range_match.group(1))
            last_byte = int(range_match.group(2)) if range_match.group(2) else file_size - 1
            
            if first_byte >= file_size:
                return HttpResponse(status=416)
            
            length = last_byte - first_byte + 1
            
            file_obj = open(cache_path, 'rb')
            response = StreamingHttpResponse(
                RangeFileWrapper(file_obj, offset=first_byte, length=length),
                status=206,
                content_type=content_type
            )
            response['Content-Length'] = length
            response['Content-Range'] = f'bytes {first_byte}-{last_byte}/{file_size}'
        else:
            response = FileResponse(open(cache_path, 'rb'), content_type=content_type)
            response['Content-Length'] = file_size
    else:
        response = FileResponse(open(cache_path, 'rb'), content_type=content_type)
        response['Content-Length'] = file_size
    
    # Common headers
    response['Accept-Ranges'] = 'bytes'
    response['Cache-Control'] = 'public, max-age=86400'
    
    # CORS headers
    origin = request.META.get('HTTP_ORIGIN', '')
    if origin:
        parsed_origin = urlparse(origin)
        origin_domain = parsed_origin.netloc.split(':')[0] if ':' in parsed_origin.netloc else parsed_origin.netloc
        if any(origin_domain == d or origin_domain.endswith('.' + d) for d in ALLOWED_DOMAINS):
            response['Access-Control-Allow-Origin'] = origin
    
    # Increment view count (only for initial request)
    if not range_header:
        media.increment_view()
    
    return response


@referrer_protected
@require_GET
def download_media(request, uid):
    """
    Download media file (supports local + Google Drive)
    URL: /media-stream/download/<uid>/
    """
    try:
        media = StreamMedia.objects.get(uid=uid, is_active=True)
    except StreamMedia.DoesNotExist:
        return HttpResponseNotFound("Media not found")
    
    # Check access
    if media.requires_login and not request.user.is_authenticated:
        return HttpResponseForbidden("Login required")
    
    if not media.is_public and not request.user.is_authenticated:
        return HttpResponseForbidden("This content is not public")
    
    # Google Drive: download from cache
    if media.storage_type == 'gdrive' and media.gdrive_file_id:
        from .gdrive import download_to_cache
        cache_path = download_to_cache(media.gdrive_file_id)
        if not cache_path:
            return HttpResponse("Failed to fetch from Google Drive", status=502)
        
        media.increment_download()
        
        ext = os.path.splitext(cache_path)[1] or '.mp4'
        safe_filename = f"{media.slug}{ext}"
        
        response = FileResponse(
            open(cache_path, 'rb'),
            as_attachment=True,
            filename=safe_filename
        )
        return response
    
    # Local storage
    try:
        file_path = media.file.path
    except (ValueError, FileNotFoundError):
        return HttpResponseNotFound("File not found")
    
    # Increment download count
    media.increment_download()
    
    # Generate safe filename
    ext = os.path.splitext(media.file.name)[1]
    safe_filename = f"{media.slug}{ext}"
    
    response = FileResponse(
        open(file_path, 'rb'),
        as_attachment=True,
        filename=safe_filename
    )
    
    return response


@referrer_protected
@require_GET  
def get_subtitle(request, subtitle_id):
    """
    Get subtitle file for media
    URL: /media-stream/subtitle/<subtitle_id>/
    """
    try:
        subtitle = MediaSubtitle.objects.get(id=subtitle_id)
    except MediaSubtitle.DoesNotExist:
        return HttpResponseNotFound("Subtitle not found")
    
    try:
        file_path = subtitle.file.path
    except (ValueError, FileNotFoundError):
        return HttpResponseNotFound("Subtitle file not found")
    
    # Determine content type
    if subtitle.file.name.endswith('.vtt'):
        content_type = 'text/vtt'
    else:
        content_type = 'text/plain'
    
    response = FileResponse(open(file_path, 'rb'), content_type=content_type)
    response['Cache-Control'] = 'public, max-age=86400'
    
    return response


# ============================================================================
# API VIEWS (for frontend)
# ============================================================================

@require_GET
def media_info(request, uid):
    """
    Get media information as JSON
    URL: /media-stream/info/<uid>/
    """
    try:
        media = StreamMedia.objects.get(uid=uid, is_active=True)
    except StreamMedia.DoesNotExist:
        return JsonResponse({'error': 'Media not found'}, status=404)
    
    # Check access
    if not media.is_public and not request.user.is_authenticated:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    subtitles = [
        {
            'language': sub.language,
            'label': sub.label,
            'url': f'/media-stream/subtitle/{media.uid}/{sub.language}/',
            'is_default': sub.is_default,
        }
        for sub in media.subtitles.all()
    ]
    
    data = {
        'uid': str(media.uid),
        'title': media.title,
        'description': media.description,
        'media_type': media.media_type,
        'stream_url': media.get_stream_url(),
        'download_url': media.get_download_url() if media.is_public else None,
        'thumbnail': media.thumbnail.url if media.thumbnail else None,
        'duration': media.duration,
        'duration_display': media.duration_display,
        'language': media.language,
        'level': media.level,
        'view_count': media.view_count,
        'subtitles': subtitles,
        'embed_code': media.get_embed_code(),
    }
    
    return JsonResponse(data)


@require_GET
def list_media(request):
    """
    List all public media
    URL: /media-stream/list/
    """
    media_type = request.GET.get('type')  # video/audio
    language = request.GET.get('language')
    level = request.GET.get('level')
    category = request.GET.get('category')
    search = request.GET.get('q')
    
    queryset = StreamMedia.objects.filter(is_active=True, is_public=True)
    
    if media_type:
        queryset = queryset.filter(media_type=media_type)
    if language:
        queryset = queryset.filter(Q(language=language) | Q(language='all'))
    if level:
        queryset = queryset.filter(Q(level=level) | Q(level='all'))
    if category:
        queryset = queryset.filter(category__slug=category)
    if search:
        queryset = queryset.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(tags__icontains=search)
        )
    
    data = []
    for media in queryset[:50]:
        data.append({
            'uid': str(media.uid),
            'title': media.title,
            'slug': media.slug,
            'media_type': media.media_type,
            'thumbnail': media.thumbnail.url if media.thumbnail else None,
            'duration_display': media.duration_display,
            'language': media.language,
            'level': media.level,
            'view_count': media.view_count,
            'stream_url': media.get_stream_url(),
        })
    
    return JsonResponse({'results': data})


@require_GET
def list_categories(request):
    """
    List all media categories
    URL: /media-stream/categories/
    """
    categories = MediaCategory.objects.all()
    
    data = [
        {
            'id': cat.id,
            'name': cat.name,
            'slug': cat.slug,
            'description': cat.description,
            'icon': cat.icon,
            'media_count': cat.media_files.filter(is_active=True, is_public=True).count(),
        }
        for cat in categories
    ]
    
    return JsonResponse({'results': data})


# ============================================================================
# ADMIN UPLOAD VIEWS
# ============================================================================

@staff_member_required
def upload_page(request):
    """
    Admin page for uploading media
    URL: /media-stream/admin/upload/
    """
    categories = MediaCategory.objects.all()
    
    context = {
        'categories': categories,
        'media_types': StreamMedia.MEDIA_TYPE_CHOICES,
        'languages': StreamMedia.LANGUAGE_CHOICES,
        'levels': StreamMedia.LEVEL_CHOICES,
    }
    
    return render(request, 'mediastream/upload.html', context)


@staff_member_required
@csrf_exempt
@require_http_methods(['POST'])
def upload_media(request):
    """
    Handle media file upload (AJAX) - supports single file or multiple files
    URL: /media-stream/admin/upload/api/
    """
    # Support both single 'file' and multiple 'files'
    files = request.FILES.getlist('files')
    if not files:
        single_file = request.FILES.get('file')
        if single_file:
            files = [single_file]
    
    if not files:
        return JsonResponse({'error': 'No file uploaded'}, status=400)
    
    # Get form data
    base_title = request.POST.get('title', '').strip()
    media_type = request.POST.get('media_type', 'video')
    description = request.POST.get('description', '')
    language = request.POST.get('language', 'all')
    level = request.POST.get('level', 'all')
    category_id = request.POST.get('category')
    is_public = request.POST.get('is_public', 'true') == 'true'
    storage_preference = request.POST.get('storage', 'auto')
    
    # Validate extensions
    allowed_video = ['.mp4', '.webm', '.ogg', '.mov', '.flv', '.avi', '.m4v']
    allowed_audio = ['.mp3', '.wav', '.m4a', '.aac', '.flac', '.wma', '.ogg']
    allowed_image = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    
    uploaded_media = []
    errors = []
    thumbnail_file = None
    
    # Separate media files from thumbnail
    media_files = []
    for f in files:
        ext = os.path.splitext(f.name)[1].lower()
        if ext in allowed_image:
            # This is a thumbnail
            thumbnail_file = f
        elif ext in allowed_video or ext in allowed_audio:
            media_files.append(f)
        else:
            errors.append(f'Unsupported format: {f.name}')
    
    if not media_files:
        return JsonResponse({'error': 'No valid media files uploaded'}, status=400)
    
    # Determine storage backend
    use_minio = False
    if storage_preference == 'minio' or (storage_preference == 'auto'):
        try:
            from .storage import is_minio_configured
            use_minio = is_minio_configured()
        except Exception:
            use_minio = False
    
    # Upload each media file
    for i, uploaded_file in enumerate(media_files):
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        
        # Determine media type from extension if not explicitly set or auto-detect
        if ext in allowed_video:
            file_media_type = 'video'
        elif ext in allowed_audio:
            file_media_type = 'audio'
        else:
            errors.append(f'Invalid format: {uploaded_file.name}')
            continue
        
        # Use specified media_type if only one file, otherwise auto-detect
        if len(media_files) == 1:
            file_media_type = media_type
        
        # Generate title
        if base_title:
            title = base_title if len(media_files) == 1 else f'{base_title} ({i+1})'
        else:
            title = os.path.splitext(uploaded_file.name)[0].replace('-', ' ').replace('_', ' ').title()
        
        try:
            media = StreamMedia(
                title=title,
                media_type=file_media_type,
                file=uploaded_file,
                description=description,
                language=language,
                level=level,
                is_public=is_public,
                uploaded_by=request.user,
            )
            
            # Add thumbnail to first media
            if thumbnail_file and i == 0:
                media.thumbnail = thumbnail_file
            
            if category_id:
                try:
                    media.category = MediaCategory.objects.get(id=category_id)
                except MediaCategory.DoesNotExist:
                    pass
            
            media.save()
            
            uploaded_media.append({
                'uid': str(media.uid),
                'title': media.title,
                'stream_url': media.get_stream_url(),
                'embed_code': media.get_embed_code(),
                'file_size': media.file_size_display,
            })
            
        except Exception as e:
            errors.append(f'{uploaded_file.name}: {str(e)}')
    
    if not uploaded_media:
        return JsonResponse({'error': 'Upload failed: ' + '; '.join(errors)}, status=500)
    
    return JsonResponse({
        'success': True,
        'media': uploaded_media if len(uploaded_media) > 1 else uploaded_media[0],
        'count': len(uploaded_media),
        'errors': errors if errors else None
    })


@staff_member_required
def manage_page(request):
    """
    Admin page for managing uploaded media
    URL: /media-stream/admin/manage/
    """
    media_type = request.GET.get('type')
    language = request.GET.get('language')
    
    queryset = StreamMedia.objects.all()
    
    if media_type:
        queryset = queryset.filter(media_type=media_type)
    if language:
        queryset = queryset.filter(language=language)
    
    context = {
        'media_list': queryset[:100],
        'media_types': StreamMedia.MEDIA_TYPE_CHOICES,
        'languages': StreamMedia.LANGUAGE_CHOICES,
        'current_type': media_type,
        'current_language': language,
    }
    
    return render(request, 'mediastream/manage.html', context)


@staff_member_required
@require_http_methods(['POST'])
def delete_media(request, uid):
    """
    Delete media file
    URL: /media-stream/admin/delete/<uid>/
    """
    try:
        media = StreamMedia.objects.get(uid=uid)
        
        # Delete file from storage
        if media.file:
            try:
                default_storage.delete(media.file.name)
            except Exception:
                pass
        
        # Delete thumbnail
        if media.thumbnail:
            try:
                default_storage.delete(media.thumbnail.name)
            except Exception:
                pass
        
        media.delete()
        
        return JsonResponse({'success': True})
    
    except StreamMedia.DoesNotExist:
        return JsonResponse({'error': 'Media not found'}, status=404)

