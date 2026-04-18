"""
Media Stream Views
Streaming video/audio với bảo vệ referrer - chỉ cho phép từ domain unstressvn.com
"""

import os
import re
import mimetypes
import logging
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
from django.contrib.auth import get_user_model
from django.core import signing
from django.conf import settings
from django.core.files.storage import default_storage
from django.db.models import Q

from .models import StreamMedia, MediaCategory, MediaSubtitle, MediaPlaylist


# ============================================================================
# UPLOAD TOKEN (for direct upload bypass Cloudflare)
# ============================================================================

def _generate_upload_token(user):
    """Generate signed upload token valid for 2 hours."""
    return signing.dumps({'uid': user.pk}, salt='direct-upload')


def _verify_upload_token(token):
    """Verify upload token, returns User or None."""
    if not token:
        return None
    User = get_user_model()
    try:
        data = signing.loads(token, salt='direct-upload', max_age=7200)
        user = User.objects.get(pk=data['uid'], is_staff=True)
        return user
    except (signing.BadSignature, signing.SignatureExpired, User.DoesNotExist, KeyError):
        return None


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
    Hỗ trợ local storage và Google Drive
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
    
    # Local file storage
    if media.file:
        return stream_from_local(request, media)
    
    return HttpResponseNotFound("No file available for this media")


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
    from .gdrive import download_to_cache, is_cached
    
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
# AUTO-PUBLISH: Create Article from uploaded media
# ============================================================================

def _auto_publish_article(media, upload_user, publish_category_id=None):
    """
    Create a news Article linked to the uploaded StreamMedia.
    Returns the article or None on failure.
    """
    from news.models import Article, Category as NewsCategory
    from django.utils import timezone
    
    try:
        # Resolve category
        category = None
        if publish_category_id:
            try:
                category = NewsCategory.objects.get(id=int(publish_category_id), is_active=True)
            except (NewsCategory.DoesNotExist, ValueError):
                pass
        
        # If no category specified, find or create "Video" category
        if not category:
            category, _created = NewsCategory.objects.get_or_create(
                slug='video',
                defaults={'name': 'Video', 'icon': 'FaVideo', 'order': 20}
            )
        
        # Build content HTML with embedded player + subtitles
        stream_url = media.get_stream_url()
        if media.media_type == 'video':
            player_html = (
                f'<div class="video-player-wrapper" style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;max-width:100%;border-radius:8px;">\n'
                f'  <video controls style="position:absolute;top:0;left:0;width:100%;height:100%;" preload="metadata"'
            )
            # Add subtitle tracks
            subtitles = list(media.subtitles.all())
            if subtitles:
                player_html += '>\n'
                for sub in subtitles:
                    default_attr = ' default' if sub.is_default else ''
                    player_html += f'    <track kind="subtitles" src="{sub.file.url}" srclang="{sub.language}" label="{sub.label}"{default_attr}>\n'
                player_html += f'    <source src="{stream_url}" type="{media.mime_type or "video/mp4"}">\n'
                player_html += '  </video>\n</div>'
            else:
                player_html += f' src="{stream_url}">\n  </video>\n</div>'
        else:
            player_html = f'<audio controls src="{stream_url}" style="width:100%;" preload="metadata"></audio>'
        
        description = media.description or ''
        content_parts = [player_html]
        if description:
            content_parts.append(f'<p>{description}</p>')
        content = '\n\n'.join(content_parts)
        
        # Create article
        article = Article(
            title=media.title,
            excerpt=description[:500] if description else f'{media.get_media_type_display()} — {media.title}',
            content=content,
            category=category,
            author=upload_user,
            is_published=True,
            published_at=timezone.now(),
            tags=media.tags or '',
        )
        # Copy thumbnail if available
        if media.thumbnail:
            article.cover_image = media.thumbnail
        article.save()
        
        logger.info('Auto-published article "%s" (id=%s) for media uid=%s', article.title, article.pk, media.uid)
        return article
    except Exception as e:
        logger.error('Auto-publish failed for media uid=%s: %s', media.uid, e, exc_info=True)
        return None


def _format_duration(seconds):
    if not seconds:
        return None
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def _extract_from_uploaded_video(uploaded_file):
    """
    Extract thumbnail + metadata from an uploaded video file BEFORE saving.
    Works with any Django UploadedFile (InMemoryUploadedFile or TemporaryUploadedFile).
    
    Returns dict: {
        'thumbnail_path': str or None,  # path to temp jpg (caller must clean up)
        'duration': int or None,
        'width': int or None,
        'height': int or None,
    }
    """
    import subprocess
    import json as _json
    import tempfile
    
    result_data = {'thumbnail_path': None, 'duration': None, 'width': None, 'height': None}
    tmp_video_path = None

    try:
        # Write uploaded file to a temp file so ffmpeg/ffprobe can read it
        ext = os.path.splitext(uploaded_file.name)[1].lower() or '.mp4'
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp_video:
            tmp_video_path = tmp_video.name
            uploaded_file.seek(0)
            for chunk in uploaded_file.chunks():
                tmp_video.write(chunk)
            uploaded_file.seek(0)  # reset for subsequent reads

        # --- ffprobe: extract metadata ---
        try:
            probe_cmd = [
                'ffprobe', '-v', 'quiet',
                '-print_format', 'json',
                '-show_format', '-show_streams',
                tmp_video_path,
            ]
            probe_result = subprocess.run(probe_cmd, capture_output=True, timeout=15, text=True)
            if probe_result.returncode == 0:
                probe = _json.loads(probe_result.stdout)
                duration_str = probe.get('format', {}).get('duration')
                if duration_str:
                    result_data['duration'] = int(float(duration_str))
                for stream in probe.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        result_data['width'] = stream.get('width')
                        result_data['height'] = stream.get('height')
                        break
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.warning('ffprobe failed for %s: %s', uploaded_file.name, e)

        # --- ffmpeg: extract thumbnail ---
        try:
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_thumb:
                thumb_path = tmp_thumb.name

            cmd = [
                'ffmpeg', '-y',
                '-i', tmp_video_path,
                '-ss', '1',           # seek to 1 second
                '-frames:v', '1',     # extract 1 frame
                '-q:v', '2',          # high quality JPEG
                '-vf', 'scale=640:-2',  # 640px wide, keep aspect ratio
                thumb_path,
            ]
            ffmpeg_result = subprocess.run(cmd, capture_output=True, timeout=30, text=True)

            if ffmpeg_result.returncode != 0:
                # Try from start if seeking fails (very short video)
                cmd[cmd.index('-ss') + 1] = '0'
                ffmpeg_result = subprocess.run(cmd, capture_output=True, timeout=30, text=True)

            if ffmpeg_result.returncode == 0 and os.path.isfile(thumb_path) and os.path.getsize(thumb_path) > 0:
                result_data['thumbnail_path'] = thumb_path
            else:
                logger.warning('ffmpeg thumbnail failed for %s: %s', uploaded_file.name,
                               ffmpeg_result.stderr[:300] if ffmpeg_result.stderr else 'unknown')
                if os.path.isfile(thumb_path):
                    os.unlink(thumb_path)
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.warning('ffmpeg failed for %s: %s', uploaded_file.name, e)

    except Exception as e:
        logger.error('Video extraction failed for %s: %s', uploaded_file.name, e, exc_info=True)
    finally:
        # Clean up temp video (but NOT the thumbnail — caller handles that)
        if tmp_video_path and os.path.isfile(tmp_video_path):
            os.unlink(tmp_video_path)

    return result_data


# ============================================================================
# ADMIN UPLOAD VIEWS
# ============================================================================

@csrf_exempt  # Required for cross-origin direct upload via X-Upload-Token signed token
@require_http_methods(['POST'])
def upload_media(request):
    """
    Handle media file upload (AJAX) - supports single file or multiple files
    URL: /media-stream/admin/upload/api/
    
    Auth: session-based (same origin) OR signed upload token (cross-origin direct upload)
    """
    # === Authentication ===
    if request.user.is_authenticated and request.user.is_staff:
        upload_user = request.user
        # For session-auth requests (same-origin), enforce CSRF protection
        from django.middleware.csrf import CsrfViewMiddleware
        _csrf_mw = CsrfViewMiddleware(lambda r: None)
        _csrf_reason = _csrf_mw.process_view(request, None, [], {})
        if _csrf_reason is not None:
            return JsonResponse({'error': 'CSRF validation failed'}, status=403)
    else:
        # Cross-origin: verify signed upload token
        token = request.META.get('HTTP_X_UPLOAD_TOKEN', '')
        upload_user = _verify_upload_token(token)
        if upload_user is None:
            return JsonResponse({'error': 'Authentication required — not staff or invalid token'}, status=403)
    
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
    storage_preference = request.POST.get('storage', 'gdrive')
    auto_publish = request.POST.get('auto_publish', 'false') == 'true'
    publish_category_id = request.POST.get('publish_category', '').strip()
    
    # Validate extensions
    allowed_video = ['.mp4', '.webm', '.ogg', '.mov', '.flv', '.avi', '.m4v']
    allowed_audio = ['.mp3', '.wav', '.m4a', '.aac', '.flac', '.wma', '.ogg']
    allowed_image = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    allowed_subs = ['.vtt', '.srt']
    
    uploaded_media = []
    errors = []
    thumbnail_file = None
    
    # Separate media files from thumbnail and subtitles
    media_files = []
    subtitle_files = []
    for f in files:
        ext = os.path.splitext(f.name)[1].lower()
        if ext in allowed_image:
            thumbnail_file = f
        elif ext in allowed_subs:
            subtitle_files.append(f)
        elif ext in allowed_video or ext in allowed_audio:
            media_files.append(f)
        else:
            errors.append(f'Unsupported format: {f.name}')
    
    if not media_files:
        return JsonResponse({'error': 'No valid media files uploaded'}, status=400)
    
    # Google Drive upload setup
    use_gdrive = storage_preference == 'gdrive'
    gdrive_account = None  # OAuth2 multi-account
    if use_gdrive:
        from . import gdrive_oauth
        from .models import GDriveAccount
        # Allow user to pick specific account
        account_id = request.POST.get('gdrive_account_id', '').strip()
        if account_id and account_id != 'auto':
            try:
                gdrive_account = GDriveAccount.objects.get(id=int(account_id), is_active=True)
            except (GDriveAccount.DoesNotExist, ValueError):
                gdrive_account = None
        if not gdrive_account:
            gdrive_account = gdrive_oauth.select_best_account()
        if not gdrive_account:
            use_gdrive = False
            errors.append('Google Drive chưa cấu hình — cần thêm tài khoản Gmail trong phần OAuth2')
    
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
                description=description,
                language=language,
                level=level,
                is_public=is_public,
                uploaded_by=upload_user,
            )
            
            # Auto-extract thumbnail + metadata from video BEFORE upload/save
            auto_thumb_path = None
            if file_media_type == 'video' and not thumbnail_file:
                extracted = _extract_from_uploaded_video(uploaded_file)
                auto_thumb_path = extracted.get('thumbnail_path')
                if extracted.get('duration'):
                    media.duration = extracted['duration']
                if extracted.get('width'):
                    media.width = extracted['width']
                if extracted.get('height'):
                    media.height = extracted['height']
            
            # Upload to Google Drive or save locally
            if use_gdrive and gdrive_account:
                try:
                    mime_type, _ = mimetypes.guess_type(uploaded_file.name)
                    result = gdrive_oauth.upload_to_account(
                        gdrive_account, uploaded_file, uploaded_file.name,
                        mime_type=mime_type or 'video/mp4',
                        media_type=file_media_type,
                    )
                    if not result.get('success'):
                        raise Exception(result.get('error', 'GDrive upload returned failure'))
                    media.storage_type = 'gdrive'
                    media.gdrive_file_id = result['file_id']
                    media.gdrive_url = result.get('gdrive_url', '')
                    media.file_size = uploaded_file.size
                    media.mime_type = mime_type or 'video/mp4'
                except Exception as e:
                    logger.error('GDrive upload failed for %s: %s', uploaded_file.name, e, exc_info=True)
                    errors.append(f'GDrive upload failed for {uploaded_file.name}: {str(e)[:200]}')
                    media.file = uploaded_file
                    media.storage_type = 'local'
            else:
                media.file = uploaded_file
                media.storage_type = 'local'
            
            # Add thumbnail: user-uploaded takes priority, then auto-extracted
            if thumbnail_file and i == 0:
                media.thumbnail = thumbnail_file
            elif auto_thumb_path:
                from django.core.files import File
                with open(auto_thumb_path, 'rb') as f:
                    media.thumbnail.save(f'{media.uid}_auto.jpg', File(f), save=False)
            
            if category_id:
                try:
                    media.category = MediaCategory.objects.get(id=category_id)
                except MediaCategory.DoesNotExist:
                    pass
            
            media.save()
            
            # Cleanup auto-thumbnail temp file
            if auto_thumb_path and os.path.isfile(auto_thumb_path):
                os.unlink(auto_thumb_path)
            
            # Attach subtitle files to the first media
            if subtitle_files and i == 0:
                for sf in subtitle_files:
                    sub_name = os.path.splitext(sf.name)[0].lower()
                    # Detect subtitle language from filename
                    sub_lang = 'vi'
                    if '_en' in sub_name or '.en' in sub_name or 'english' in sub_name:
                        sub_lang = 'en'
                    elif '_de' in sub_name or '.de' in sub_name or 'deutsch' in sub_name or 'german' in sub_name:
                        sub_lang = 'de'
                    try:
                        from .models import MediaSubtitle
                        MediaSubtitle.objects.create(
                            media=media,
                            language=sub_lang,
                            label=sf.name,
                            file=sf,
                            is_default=(sub_lang == language),
                        )
                    except Exception as e:
                        errors.append(f'Subtitle {sf.name}: {str(e)[:80]}')
            
            uploaded_media.append({
                'uid': str(media.uid),
                'title': media.title,
                'stream_url': media.get_stream_url(),
                'embed_code': media.get_embed_code(),
                'file_size': media.file_size_display,
                'storage_type': media.storage_type,
                'thumbnail_url': media.thumbnail.url if media.thumbnail else None,
                'duration': media.duration,
                'duration_formatted': _format_duration(media.duration),
                'gdrive_account': gdrive_account.email if gdrive_account and media.storage_type == 'gdrive' else None,
                'subtitles': [
                    {'language': s.language, 'label': s.label, 'url': s.file.url if s.file else ''}
                    for s in media.subtitles.all()
                ],
                'article_url': None,
            })
            
            # Auto-publish article if requested
            if auto_publish:
                article = _auto_publish_article(media, upload_user, publish_category_id)
                if article:
                    uploaded_media[-1]['article_url'] = article.get_absolute_url()
                    uploaded_media[-1]['article_id'] = article.pk
                else:
                    errors.append(f'Auto-publish failed for {media.title}')
            
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


logger = logging.getLogger(__name__)


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


# ============================================================================
# GDRIVE OAUTH2 MULTI-ACCOUNT VIEWS
# ============================================================================

@staff_member_required
def gdrive_oauth_authorize(request):
    """Redirect admin to Google OAuth2 consent screen."""
    from . import gdrive_oauth
    redirect_uri = request.build_absolute_uri('/media-stream/admin/gdrive/callback/')
    if not request.is_secure() and not settings.DEBUG:
        redirect_uri = redirect_uri.replace('http://', 'https://')
    url = gdrive_oauth.get_authorize_url(redirect_uri)
    if not url:
        return HttpResponse(
            '<h3>⚠️ Chưa cấu hình OAuth2</h3>'
            '<p>Vào Django Admin → Cấu hình hệ thống → Google Drive OAuth2 → nhập Client ID và Client Secret.</p>'
            '<p><a href="/admin/core/siteconfiguration/">→ Cấu hình hệ thống</a></p>',
            content_type='text/html; charset=utf-8',
        )
    from django.shortcuts import redirect as http_redirect
    return http_redirect(url)


@staff_member_required
def gdrive_oauth_callback(request):
    """Handle OAuth2 callback from Google."""
    from . import gdrive_oauth
    from .models import GDriveAccount

    error = request.GET.get('error')
    if error:
        return HttpResponse(
            f'<h3>❌ Google từ chối: {error}</h3>'
            '<p><a href="/admin/mediastream/streammedia/">← Quay lại</a></p>',
            content_type='text/html; charset=utf-8',
        )

    code = request.GET.get('code')
    if not code:
        return HttpResponse(
            '<h3>❌ Không nhận được authorization code</h3>',
            content_type='text/html; charset=utf-8', status=400,
        )

    redirect_uri = request.build_absolute_uri('/media-stream/admin/gdrive/callback/')
    if not request.is_secure() and not settings.DEBUG:
        redirect_uri = redirect_uri.replace('http://', 'https://')

    tokens, err = gdrive_oauth.exchange_code_for_tokens(code, redirect_uri)
    if err:
        return HttpResponse(
            f'<h3>❌ Lỗi lấy token: {err}</h3>'
            '<p><a href="/admin/mediastream/streammedia/">← Quay lại</a></p>',
            content_type='text/html; charset=utf-8',
        )

    email = gdrive_oauth.get_account_email(tokens['access_token'])
    if not email:
        return HttpResponse(
            '<h3>❌ Không lấy được email từ Google</h3>',
            content_type='text/html; charset=utf-8', status=500,
        )

    account, created = GDriveAccount.objects.update_or_create(
        email=email,
        defaults={
            'refresh_token': tokens['refresh_token'],
            'is_active': True,
        },
    )

    gdrive_oauth.update_storage_info(account)
    gdrive_oauth.ensure_account_folders(account)

    action = 'Thêm mới' if created else 'Cập nhật'
    return HttpResponse(
        f'<h3>✅ {action} tài khoản: {email}</h3>'
        f'<p>Dung lượng: {account.storage_used_display} / {account.storage_total_display}</p>'
        '<p>Đang chuyển hướng...</p>'
        '<script>setTimeout(function(){ window.location.href="/admin/mediastream/streammedia/"; }, 2000);</script>',
        content_type='text/html; charset=utf-8',
    )


@staff_member_required
@require_http_methods(['GET'])
def gdrive_accounts_api(request):
    """API: List all GDrive accounts with storage info."""
    from .models import GDriveAccount
    accounts = GDriveAccount.objects.all().order_by('-is_active', 'storage_used')
    data = []
    for acc in accounts:
        data.append({
            'id': acc.id,
            'email': acc.email,
            'is_active': acc.is_active,
            'storage_used': acc.storage_used,
            'storage_total': acc.storage_total,
            'storage_free': acc.storage_free,
            'storage_percent': acc.storage_percent,
            'storage_used_display': acc.storage_used_display,
            'storage_total_display': acc.storage_total_display,
            'storage_free_display': acc.storage_free_display,
            'last_used': acc.last_used.isoformat() if acc.last_used else None,
            'folder_mapping': acc.folder_mapping,
        })
    return JsonResponse({'accounts': data})


@staff_member_required
@require_http_methods(['POST'])
def gdrive_update_storage(request, account_id):
    """API: Refresh storage info for an account."""
    from .models import GDriveAccount
    from . import gdrive_oauth
    try:
        account = GDriveAccount.objects.get(id=account_id)
        token_status = gdrive_oauth.check_token_status(account)
        success = gdrive_oauth.update_storage_info(account)
        if success:
            return JsonResponse({
                'success': True,
                'storage_used': account.storage_used,
                'storage_total': account.storage_total,
                'storage_percent': account.storage_percent,
                'storage_used_display': account.storage_used_display,
                'storage_free_display': account.storage_free_display,
                'token_valid': token_status['valid'],
                'token_error': token_status['error'],
            })
        return JsonResponse({
            'success': False,
            'error': 'Không thể kết nối',
            'token_valid': token_status['valid'],
            'token_error': token_status['error'],
        }, status=500)
    except GDriveAccount.DoesNotExist:
        return JsonResponse({'error': 'Account not found'}, status=404)


@staff_member_required
@require_http_methods(['POST'])
def gdrive_delete_account(request, account_id):
    """API: Delete a GDrive account."""
    from .models import GDriveAccount
    try:
        account = GDriveAccount.objects.get(id=account_id)
        email = account.email
        account.delete()
        return JsonResponse({'success': True, 'email': email})
    except GDriveAccount.DoesNotExist:
        return JsonResponse({'error': 'Account not found'}, status=404)


@staff_member_required
@require_http_methods(['POST'])
def gdrive_oauth_upload_json(request):
    """
    API: Upload OAuth2 JSON credentials file.
    Accepts the JSON file downloaded from Google Cloud Console.
    Auto-parses client_id + client_secret, saves to SiteConfiguration,
    and returns status.
    """
    import json as _json
    from core.models import SiteConfiguration

    # Accept either file upload or JSON body
    json_str = None
    if request.FILES.get('json_file'):
        json_str = request.FILES['json_file'].read().decode('utf-8')
    else:
        json_str = request.body.decode('utf-8')

    if not json_str or not json_str.strip():
        return JsonResponse({'error': 'Không nhận được file JSON'}, status=400)

    try:
        data = _json.loads(json_str)
    except _json.JSONDecodeError as e:
        return JsonResponse({'error': f'File JSON không hợp lệ: {e}'}, status=400)

    # Google OAuth2 JSON can be nested under "web" or "installed"
    inner = data.get('web') or data.get('installed') or data
    client_id = inner.get('client_id', '').strip()
    client_secret = inner.get('client_secret', '').strip()
    project_id = inner.get('project_id', '')
    redirect_uris = inner.get('redirect_uris', [])

    if not client_id or not client_secret:
        return JsonResponse({
            'error': 'File JSON thiếu client_id hoặc client_secret. '
                     'Hãy tải file JSON từ Google Cloud Console → Credentials → OAuth 2.0 Client ID.'
        }, status=400)

    # Save to SiteConfiguration
    config = SiteConfiguration.get_instance()
    config.gdrive_oauth_client_id = client_id
    config.gdrive_oauth_client_secret = client_secret
    config.save(update_fields=['gdrive_oauth_client_id', 'gdrive_oauth_client_secret'])

    # Check configured redirect URI
    expected_redirect = request.build_absolute_uri('/media-stream/admin/gdrive/callback/')
    if not request.is_secure() and not settings.DEBUG:
        expected_redirect = expected_redirect.replace('http://', 'https://')
    redirect_ok = any(expected_redirect in uri for uri in redirect_uris)

    return JsonResponse({
        'success': True,
        'client_id': client_id[:20] + '...' if len(client_id) > 20 else client_id,
        'project_id': project_id,
        'redirect_uris': redirect_uris,
        'redirect_ok': redirect_ok,
        'expected_redirect': expected_redirect,
    })


@staff_member_required
@require_http_methods(['GET'])
def gdrive_oauth_status(request):
    """
    API: Check OAuth2 configuration status.
    Returns current config state + number of connected accounts.
    """
    from core.models import SiteConfiguration
    from .models import GDriveAccount

    config = SiteConfiguration.get_instance()
    client_id = (config.gdrive_oauth_client_id or '').strip()
    client_secret = (config.gdrive_oauth_client_secret or '').strip()
    configured = bool(client_id and client_secret)

    accounts = GDriveAccount.objects.filter(is_active=True)
    account_count = accounts.count()
    total_free = sum(a.storage_free for a in accounts)
    total_storage = sum(a.storage_total for a in accounts)

    return JsonResponse({
        'configured': configured,
        'client_id_preview': (client_id[:20] + '...') if len(client_id) > 20 else client_id,
        'account_count': account_count,
        'total_free': total_free,
        'total_storage': total_storage,
        'total_free_display': _format_bytes(total_free),
        'total_storage_display': _format_bytes(total_storage),
    })


def _format_bytes(b):
    """Format bytes to human-readable string."""
    if b <= 0:
        return '0 B'
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if b < 1024:
            return f'{b:.1f} {unit}'
        b /= 1024
    return f'{b:.1f} PB'
