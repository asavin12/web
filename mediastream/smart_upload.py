"""
Smart Upload API — Upload video + subtitle, AI phân tích nội dung phụ đề
để tự tạo tiêu đề, mô tả, tags cho StreamMedia.

Endpoints:
  POST /media-stream/smart-upload/           — Upload video + sub, AI generate metadata
  POST /media-stream/analyze-subtitle/       — Phân tích subtitle bằng Gemini (preview)
  GET  /media-stream/api/gemini-key-status/  — Check Gemini key status (admin)
  POST /media-stream/api/gemini-key/         — Save Gemini key (admin)
  GET  /media-stream/api/gdrive-status/      — Check GDrive connection (admin)
  POST /media-stream/api/gdrive-credentials/ — Save GDrive Service Account (admin)
  POST /media-stream/api/gdrive-check/       — Test GDrive connection (admin)
  GET  /media-stream/api/gdrive-folders/     — List GDrive folders (admin)
  POST /media-stream/api/gdrive-folder/      — Save default folder (admin)
"""

import os
import json
import logging
import re

from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.base import ContentFile
from django.utils.text import slugify

from .models import StreamMedia, MediaCategory, MediaSubtitle

logger = logging.getLogger(__name__)


# ============================================================================
# Subtitle Parsing
# ============================================================================

def parse_subtitle_text(content, filename=''):
    """
    Parse .vtt or .srt content → list of text segments.
    Returns: list[str] — pure text lines (no timestamps)
    """
    lines = content.strip().split('\n')
    texts = []
    is_srt = filename.lower().endswith('.srt') or (not filename and '-->' in content and 'WEBVTT' not in content)

    i = 0
    # Skip WEBVTT header
    if not is_srt:
        while i < len(lines) and '-->' not in lines[i]:
            i += 1

    while i < len(lines):
        line = lines[i].strip()
        if '-->' in line:
            # Timestamp line — collect text until blank or next cue
            i += 1
            while i < len(lines) and lines[i].strip() and '-->' not in lines[i]:
                text = lines[i].strip()
                # Skip numeric cue IDs
                if not text.isdigit():
                    # Strip HTML tags
                    text = re.sub(r'<[^>]+>', '', text)
                    if text:
                        texts.append(text)
                i += 1
        else:
            i += 1

    return texts


def detect_subtitle_language(texts):
    """
    Heuristic detect language from subtitle text.
    Returns: 'de' | 'en' | 'vi' | 'all'
    """
    sample = ' '.join(texts[:50]).lower()

    # German markers
    de_markers = ['ich', 'und', 'der', 'die', 'das', 'ist', 'nicht', 'ein', 'eine',
                  'haben', 'werden', 'können', 'möchte', 'ü', 'ö', 'ä', 'ß']
    de_score = sum(1 for m in de_markers if f' {m} ' in f' {sample} ' or m in sample)

    # English markers
    en_markers = ['the', 'and', 'you', 'that', 'this', 'with', 'have', 'from',
                  'they', 'been', 'would', 'could', 'should']
    en_score = sum(1 for m in en_markers if f' {m} ' in f' {sample} ')

    # Vietnamese markers
    vi_markers = ['của', 'và', 'là', 'được', 'không', 'có', 'trong', 'này',
                  'với', 'cho', 'một', 'những', 'đã', 'về', 'từ']
    vi_score = sum(1 for m in vi_markers if m in sample)

    scores = {'de': de_score, 'en': en_score, 'vi': vi_score}
    best = max(scores, key=scores.get)
    if scores[best] < 3:
        return 'all'
    return best


# ============================================================================
# Gemini AI Analysis
# ============================================================================

def _get_gemini_key():
    """Get Gemini API key from SiteConfiguration or return None."""
    try:
        from core.models import SiteConfiguration
        config = SiteConfiguration.get_instance()
        if config and config.gemini_api_key:
            return config.gemini_api_key
    except Exception as e:
        logger.error(f"Error getting Gemini API key: {e}")
    return None


def analyze_subtitle_with_gemini(texts, language='auto', user_api_key=None):
    """
    Gửi nội dung subtitle cho Gemini để phân tích và sinh metadata.

    Returns: {
        'title': str,
        'description': str,
        'tags': str (comma-separated),
        'level': str (A1-C2),
        'key_phrases': list[str],
        'language_detected': str,
    }
    """
    api_key = user_api_key or _get_gemini_key()
    if not api_key:
        return None

    import google.generativeai as genai
    genai.configure(api_key=api_key)

    # Take a representative sample (not too long)
    sample_lines = texts[:100]
    subtitle_text = '\n'.join(sample_lines)

    lang_hint = {
        'de': 'tiếng Đức', 'en': 'tiếng Anh', 'vi': 'tiếng Việt',
        'all': 'đa ngôn ngữ', 'auto': 'tự nhận diện'
    }.get(language, language)

    prompt = f"""Bạn là trợ lý AI phân tích nội dung phụ đề video học ngoại ngữ.
Ngôn ngữ phụ đề: {lang_hint}

Dựa vào nội dung phụ đề bên dưới, hãy phân tích và trả về JSON (KHÔNG markdown, CHỈ JSON):

{{
  "title": "Tiêu đề hấp dẫn cho video (tiếng Việt, ≤80 ký tự). Nêu rõ chủ đề/cấu trúc câu nổi bật nếu có.",
  "description": "Mô tả chi tiết nội dung video (tiếng Việt, 2-3 câu). Nêu rõ người xem sẽ học được gì.",
  "tags": "từ khóa phân cách bằng dấu phẩy (5-10 tags, tiếng Việt + ngôn ngữ gốc)",
  "level": "Trình độ phù hợp: A1|A2|B1|B2|C1|C2|all",
  "key_phrases": ["cụm từ/cấu trúc câu đặc trưng tìm thấy trong phụ đề (tối đa 5)"],
  "language_detected": "de|en|vi|all"
}}

NỘI DUNG PHỤ ĐỀ:
{subtitle_text}"""

    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        result_text = response.text.strip()

        # Strip markdown code fences if present
        if result_text.startswith('```'):
            result_text = re.sub(r'^```(?:json)?\s*', '', result_text)
            result_text = re.sub(r'\s*```$', '', result_text)

        return json.loads(result_text)
    except json.JSONDecodeError as e:
        logger.warning(f"Gemini returned invalid JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Gemini analysis error: {e}")
        return None


# ============================================================================
# API Endpoints
# ============================================================================

@staff_member_required
@csrf_exempt
@require_POST
def analyze_subtitle_api(request):
    """
    Phân tích subtitle bằng AI — trả về gợi ý title/description/tags.
    Dùng cho preview trước khi upload.

    POST /media-stream/analyze-subtitle/
    Body: multipart (subtitle file) hoặc JSON (subtitle_text)
    """
    # Get subtitle content
    sub_file = request.FILES.get('subtitle')
    subtitle_text = ''
    filename = ''

    if sub_file:
        filename = sub_file.name
        try:
            raw = sub_file.read()
            subtitle_text = raw.decode('utf-8', errors='replace')
        except Exception as e:
            return JsonResponse({'error': f'Không đọc được file: {e}'}, status=400)
    else:
        try:
            body = json.loads(request.body)
            subtitle_text = body.get('subtitle_text', '')
            filename = body.get('filename', '')
        except (json.JSONDecodeError, ValueError):
            subtitle_text = request.POST.get('subtitle_text', '')

    if not subtitle_text.strip():
        return JsonResponse({'error': 'Không có nội dung phụ đề'}, status=400)

    # Parse subtitle
    texts = parse_subtitle_text(subtitle_text, filename)
    if not texts:
        return JsonResponse({'error': 'Không parse được nội dung phụ đề'}, status=400)

    # Detect language
    detected_lang = detect_subtitle_language(texts)

    # Get user-provided Gemini key (from header or body)
    user_key = request.META.get('HTTP_X_GEMINI_KEY', '')
    if not user_key:
        try:
            body = json.loads(request.body)
            user_key = body.get('gemini_api_key', '')
        except Exception:
            user_key = request.POST.get('gemini_api_key', '')

    # Run AI analysis
    analysis = analyze_subtitle_with_gemini(texts, detected_lang, user_key or None)

    if not analysis:
        # Fallback: generate basic metadata without AI
        title_sample = texts[0][:60] if texts else 'Video học ngoại ngữ'
        lang_name = {'de': 'tiếng Đức', 'en': 'tiếng Anh', 'vi': 'tiếng Việt'}.get(
            detected_lang, 'ngoại ngữ')
        return JsonResponse({
            'success': True,
            'ai_powered': False,
            'reason': 'Gemini API key chưa được cấu hình hoặc lỗi API',
            'analysis': {
                'title': f'Học {lang_name} qua video — {title_sample}',
                'description': f'Video học {lang_name} với phụ đề song ngữ.',
                'tags': f'{lang_name}, học ngoại ngữ, video, phụ đề',
                'level': 'all',
                'key_phrases': texts[:3],
                'language_detected': detected_lang,
            },
            'subtitle_stats': {
                'total_lines': len(texts),
                'sample': texts[:5],
            },
        })

    return JsonResponse({
        'success': True,
        'ai_powered': True,
        'analysis': analysis,
        'subtitle_stats': {
            'total_lines': len(texts),
            'sample': texts[:5],
        },
    })


@staff_member_required
@csrf_exempt
@require_POST
def smart_upload_api(request):
    """
    Smart upload: video + subtitle → AI analysis → tạo StreamMedia + MediaSubtitle.

    POST /media-stream/smart-upload/
    Content-Type: multipart/form-data

    Fields:
      video        — Video file (required nếu không có gdrive_url)
      gdrive_url   — Google Drive URL (thay video file)
      subtitle     — Subtitle file (.vtt/.srt) (optional)
      subtitle_lang — Ngôn ngữ subtitle: de|en|vi (default: auto-detect)

      title        — Override AI title (optional)
      description  — Override AI description (optional)
      tags         — Override AI tags (optional)
      level        — Override AI level (optional)
      language     — Ngôn ngữ video: de|en|vi|all (default: auto from subtitle)
      category     — Category ID hoặc slug (optional)
      media_type   — video|audio (default: video)
      is_public    — true|false (default: true)

      gemini_api_key — User Gemini key (optional, falls back to server key)

    Returns: created StreamMedia info + AI analysis
    """
    video_file = request.FILES.get('video')
    gdrive_url = request.POST.get('gdrive_url', '').strip()
    subtitle_file = request.FILES.get('subtitle')

    upload_to_gdrive_flag = request.POST.get('upload_to_gdrive', '').lower() == 'true'
    gdrive_folder = request.POST.get('gdrive_folder_id', '').strip()

    if not video_file and not gdrive_url:
        return JsonResponse({
            'error': 'Cần ít nhất video file hoặc Google Drive URL'
        }, status=400)

    # --- AI Analysis from subtitle ---
    ai_analysis = None
    subtitle_texts = []
    subtitle_content = ''
    subtitle_filename = ''

    if subtitle_file:
        subtitle_filename = subtitle_file.name
        try:
            raw = subtitle_file.read()
            subtitle_content = raw.decode('utf-8', errors='replace')
            subtitle_file.seek(0)  # Reset for later save
        except Exception as e:
            logger.warning(f"Could not read subtitle file: {e}")

        if subtitle_content:
            subtitle_texts = parse_subtitle_text(subtitle_content, subtitle_filename)

            user_key = request.POST.get('gemini_api_key', '') or request.META.get('HTTP_X_GEMINI_KEY', '')
            detected_lang = detect_subtitle_language(subtitle_texts)
            ai_analysis = analyze_subtitle_with_gemini(
                subtitle_texts, detected_lang, user_key or None
            )

    # --- Resolve metadata (user overrides > AI > defaults) ---
    def pick(field, ai_field=None, default=''):
        user_val = request.POST.get(field, '').strip()
        if user_val:
            return user_val
        if ai_analysis and ai_analysis.get(ai_field or field):
            return ai_analysis[ai_field or field]
        return default

    # If video file, use filename for default title
    default_title = ''
    if video_file:
        default_title = os.path.splitext(video_file.name)[0].replace('-', ' ').replace('_', ' ').title()
    elif gdrive_url:
        default_title = 'Video từ Google Drive'

    title = pick('title', default=default_title)
    description = pick('description', default='')
    tags = pick('tags', default='')
    level = pick('level', default='all')

    # Language
    language = request.POST.get('language', '').strip()
    if not language:
        if ai_analysis and ai_analysis.get('language_detected'):
            language = ai_analysis['language_detected']
        elif subtitle_texts:
            language = detect_subtitle_language(subtitle_texts)
        else:
            language = 'all'

    media_type = request.POST.get('media_type', 'video')
    is_public = request.POST.get('is_public', 'true').lower() != 'false'

    # --- Category ---
    category = None
    category_input = request.POST.get('category', '').strip()
    if category_input:
        if category_input.isdigit():
            category = MediaCategory.objects.filter(id=int(category_input)).first()
        else:
            category = MediaCategory.objects.filter(slug=category_input).first()

    # --- Create StreamMedia ---
    try:
        media = StreamMedia(
            title=title[:255],
            media_type=media_type,
            description=description,
            language=language,
            level=level,
            tags=tags[:500] if tags else '',
            category=category,
            is_public=is_public,
            uploaded_by=request.user,
        )

        if video_file and upload_to_gdrive_flag:
            # Upload local file → Google Drive → save GDrive URL
            from .gdrive_upload import upload_to_gdrive as gdrive_upload_fn
            import mimetypes as mt
            mime = mt.guess_type(video_file.name)[0] or 'video/mp4'
            upload_result = gdrive_upload_fn(
                video_file, video_file.name, mime, gdrive_folder or None
            )
            if not upload_result['success']:
                return JsonResponse({'error': upload_result['error']}, status=500)
            media.gdrive_url = upload_result['gdrive_url']
            media.gdrive_file_id = upload_result['file_id']
            media.storage_type = 'gdrive'
        elif video_file:
            media.file = video_file
        elif gdrive_url:
            media.gdrive_url = gdrive_url

        media.save()

    except Exception as e:
        logger.error(f"Smart upload error creating media: {e}", exc_info=True)
        return JsonResponse({
            'error': f'Lỗi tạo media: {str(e)[:300]}'
        }, status=500)

    # --- Save subtitle ---
    subtitle_info = None
    if subtitle_file and subtitle_content:
        sub_lang = request.POST.get('subtitle_lang', '').strip()
        if not sub_lang:
            sub_lang = detect_subtitle_language(subtitle_texts) if subtitle_texts else 'de'

        # Convert SRT → VTT if needed
        save_content = subtitle_content
        save_filename = subtitle_filename
        if subtitle_filename.lower().endswith('.srt'):
            save_content = srt_to_vtt(subtitle_content)
            save_filename = os.path.splitext(subtitle_filename)[0] + '.vtt'

        try:
            sub = MediaSubtitle(
                media=media,
                language=sub_lang,
            )
            sub.file.save(save_filename, ContentFile(save_content.encode('utf-8')), save=True)
            subtitle_info = {
                'id': sub.id,
                'language': sub.language,
                'label': sub.label,
                'lines': len(subtitle_texts),
            }
        except Exception as e:
            logger.warning(f"Could not save subtitle: {e}")

    # --- Response ---
    response_data = {
        'success': True,
        'media': {
            'uid': str(media.uid),
            'title': media.title,
            'slug': media.slug,
            'media_type': media.media_type,
            'storage_type': media.storage_type,
            'language': media.language,
            'level': media.level,
            'stream_url': media.get_stream_url(),
            'url': f'/stream/{media.uid}',
        },
        'subtitle': subtitle_info,
        'ai_analysis': ai_analysis,
        'ai_powered': ai_analysis is not None,
        'uploaded_to_gdrive': upload_to_gdrive_flag and video_file is not None,
    }

    return JsonResponse(response_data, status=201)


# ============================================================================
# Gemini API Key Management (admin)
# ============================================================================

@staff_member_required
@csrf_exempt
@require_http_methods(['GET'])
def gemini_key_status(request):
    """
    Check nếu Gemini API key đã được cấu hình trên server.
    GET /media-stream/api/gemini-key-status/
    """
    key = _get_gemini_key()
    has_key = bool(key)
    prefix = key[:8] + '...' if key and len(key) > 8 else ''

    return JsonResponse({
        'configured': has_key,
        'key_prefix': prefix if has_key else None,
    })


@staff_member_required
@csrf_exempt
@require_POST
def save_gemini_key(request):
    """
    Lưu Gemini API key vào SiteConfiguration (admin only).
    POST /media-stream/api/gemini-key/
    Body JSON: {"gemini_api_key": "AIza..."}
    """
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    new_key = body.get('gemini_api_key', '').strip()
    if not new_key:
        return JsonResponse({'error': 'Thiếu gemini_api_key'}, status=400)

    # Basic validation
    if len(new_key) < 10:
        return JsonResponse({'error': 'API key quá ngắn'}, status=400)

    try:
        from core.models import SiteConfiguration
        config = SiteConfiguration.get_instance()
        config.gemini_api_key = new_key
        config.save()

        return JsonResponse({
            'success': True,
            'message': 'Đã lưu Gemini API key thành công',
            'key_prefix': new_key[:8] + '...',
        })
    except Exception as e:
        logger.error(f"Error saving Gemini key: {e}", exc_info=True)
        return JsonResponse({
            'error': f'Lỗi lưu key: {str(e)[:200]}'
        }, status=500)


# ============================================================================
# Google Drive Credentials Management (admin)
# ============================================================================

@staff_member_required
@csrf_exempt
@require_http_methods(['GET'])
def gdrive_status(request):
    """
    Check Google Drive connection status.
    GET /media-stream/api/gdrive-status/
    """
    from .gdrive_upload import check_gdrive_connection as _check
    result = _check()

    from core.models import SiteConfiguration
    config = SiteConfiguration.get_instance()
    folder_id = config.gdrive_folder_id or ''

    return JsonResponse({
        'configured': result['connected'],
        'email': result['email'],
        'folder_id': folder_id,
        'folder_name': result['folder_name'],
        'folder_accessible': result['folder_accessible'],
        'error': result['error'],
        'visible_folders': result.get('visible_folders', []),
    })


@staff_member_required
@csrf_exempt
@require_POST
def save_gdrive_credentials(request):
    """
    Lưu Google Drive Service Account JSON + folder ID.
    POST /media-stream/api/gdrive-credentials/
    Body JSON: {"service_account_json": "{...}", "folder_id": "abc123"}
    """
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    sa_json_str = body.get('service_account_json', '').strip()
    folder_id = body.get('folder_id', '').strip()

    if not sa_json_str:
        return JsonResponse({'error': 'Thiếu service_account_json'}, status=400)

    # Validate JSON structure
    try:
        sa_dict = json.loads(sa_json_str)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Service Account JSON không hợp lệ'}, status=400)

    required_fields = ['type', 'project_id', 'private_key', 'client_email']
    missing = [f for f in required_fields if f not in sa_dict]
    if missing:
        return JsonResponse({
            'error': f'JSON thiếu các trường bắt buộc: {", ".join(missing)}'
        }, status=400)

    if sa_dict.get('type') != 'service_account':
        return JsonResponse({'error': 'JSON phải có type="service_account"'}, status=400)

    # Test connection before saving
    from .gdrive_upload import check_gdrive_connection as _check
    test = _check(sa_json_str)
    if not test['connected']:
        return JsonResponse({
            'error': f'Không kết nối được: {test["error"]}'
        }, status=400)

    # Save to SiteConfiguration
    try:
        from core.models import SiteConfiguration
        config = SiteConfiguration.get_instance()
        config.gdrive_service_account_json = sa_json_str
        if folder_id:
            config.gdrive_folder_id = folder_id
        config.save()

        return JsonResponse({
            'success': True,
            'message': 'Đã lưu Google Drive credentials',
            'email': test['email'],
            'folder_name': test.get('folder_name', ''),
        })
    except Exception as e:
        logger.error(f"Error saving GDrive credentials: {e}", exc_info=True)
        return JsonResponse({'error': f'Lỗi lưu: {str(e)[:200]}'}, status=500)


@staff_member_required
@csrf_exempt
@require_POST
def gdrive_check_connection(request):
    """
    Test Google Drive connection (có thể dùng JSON tạm để test trước khi lưu).
    POST /media-stream/api/gdrive-check/
    Body JSON (optional): {"service_account_json": "{...}"}
    """
    sa_json_str = None
    try:
        body = json.loads(request.body)
        sa_json_str = body.get('service_account_json', '').strip() or None
    except (json.JSONDecodeError, ValueError):
        pass

    from .gdrive_upload import check_gdrive_connection as _check
    result = _check(sa_json_str)

    return JsonResponse(result)


@staff_member_required
@csrf_exempt
@require_http_methods(['GET'])
def gdrive_list_folders(request):
    """
    List folders inside a GDrive folder.
    GET /media-stream/api/gdrive-folders/?parent=FOLDER_ID
    Also returns connection status so UI can distinguish
    'no subfolders' from 'not configured'.
    """
    parent = request.GET.get('parent', '').strip() or None

    from .gdrive_upload import list_gdrive_folders
    folders = list_gdrive_folders(parent)

    # Include connection info for UI
    from core.models import SiteConfiguration
    config = SiteConfiguration.get_instance()
    folder_id = config.gdrive_folder_id or ''

    result = {'folders': folders, 'configured_folder_id': folder_id}

    # If no parent specified and default folder is configured, include its name
    if not parent and folder_id:
        from .gdrive_upload import check_gdrive_connection as _check
        status = _check()
        result['folder_name'] = status.get('folder_name', '')
        result['connected'] = status.get('connected', False)
        result['folder_accessible'] = status.get('folder_accessible', False)
    else:
        result['folder_name'] = ''
        result['connected'] = bool(folder_id)
        result['folder_accessible'] = False

    return JsonResponse(result)


@staff_member_required
@csrf_exempt
@require_POST
def save_gdrive_folder(request):
    """
    Update default GDrive folder ID.
    POST /media-stream/api/gdrive-folder/
    Body JSON: {"folder_id": "abc123"}
    """
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    folder_id = body.get('folder_id', '').strip()

    try:
        from core.models import SiteConfiguration
        config = SiteConfiguration.get_instance()
        config.gdrive_folder_id = folder_id
        config.save()
        return JsonResponse({'success': True, 'folder_id': folder_id})
    except Exception as e:
        return JsonResponse({'error': str(e)[:200]}, status=500)


# ============================================================================
# Helpers
# ============================================================================

def srt_to_vtt(srt_content):
    """Convert SRT format to VTT format."""
    lines = srt_content.strip().split('\n')
    vtt_lines = ['WEBVTT', '']
    for line in lines:
        # Replace SRT timestamp format (00:00:00,000) with VTT (00:00:00.000)
        line = re.sub(r'(\d{2}:\d{2}:\d{2}),(\d{3})', r'\1.\2', line)
        vtt_lines.append(line)
    return '\n'.join(vtt_lines)
