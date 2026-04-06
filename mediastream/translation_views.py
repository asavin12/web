"""
Gemini API Translation Views
Dịch phụ đề realtime bằng Google Gemini API
Hỗ trợ cache để tránh dịch lại nội dung đã xử lý
"""

import json
import hashlib
import logging

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Cache timeout: 7 days (subtitles don't change often)
TRANSLATION_CACHE_TIMEOUT = 60 * 60 * 24 * 7

# Supported languages for translation
SUPPORTED_LANGUAGES = {
    'vi': 'Vietnamese',
    'en': 'English',
    'de': 'German',
    'fr': 'French',
    'ja': 'Japanese',
    'ko': 'Korean',
    'zh': 'Chinese',
}


def _get_gemini_api_key():
    """Get Gemini API key from SiteConfiguration"""
    try:
        from core.models import SiteConfiguration
        config = SiteConfiguration.get_instance()
        if config and config.gemini_api_key:
            return config.gemini_api_key
    except Exception as e:
        logger.error(f"Error getting Gemini API key: {e}")
    return None


def _parse_vtt_content(vtt_text):
    """
    Parse VTT content into segments
    Returns list of {index, start, end, text}
    """
    segments = []
    lines = vtt_text.strip().split('\n')
    
    i = 0
    # Skip WEBVTT header
    while i < len(lines) and not '-->' in lines[i]:
        i += 1
    
    segment_index = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if '-->' in line:
            # Timestamp line
            parts = line.split('-->')
            start = parts[0].strip()
            end = parts[1].strip()
            
            # Collect text lines until empty line or next timestamp
            text_lines = []
            i += 1
            while i < len(lines) and lines[i].strip() and '-->' not in lines[i]:
                # Skip numeric cue identifiers
                if not lines[i].strip().isdigit():
                    text_lines.append(lines[i].strip())
                i += 1
            
            if text_lines:
                segments.append({
                    'index': segment_index,
                    'start': start,
                    'end': end,
                    'text': ' '.join(text_lines),
                })
                segment_index += 1
        else:
            i += 1
    
    return segments


def _rebuild_vtt(segments):
    """Rebuild VTT content from translated segments"""
    lines = ['WEBVTT', '']
    
    for seg in segments:
        lines.append(str(seg['index'] + 1))
        lines.append(f"{seg['start']} --> {seg['end']}")
        lines.append(seg['text'])
        lines.append('')
    
    return '\n'.join(lines)


DEFAULT_GEMINI_MODEL = 'gemini-2.5-flash'

# Cache key for dynamic model list  
GEMINI_MODELS_CACHE_KEY = 'gemini_models_list'
GEMINI_MODELS_CACHE_TIMEOUT = 60 * 60 * 24  # 24h

# Fallback models when no dynamic list cached yet
GEMINI_MODELS_FALLBACK = [
    {'id': 'gemini-2.5-flash', 'name': 'Gemini 2.5 Flash', 'description': 'Nhanh, suy luận tốt'},
    {'id': 'gemini-2.5-flash-lite', 'name': 'Gemini 2.5 Flash Lite', 'description': 'Nhanh nhất, tiết kiệm'},
    {'id': 'gemini-2.5-pro', 'name': 'Gemini 2.5 Pro', 'description': 'Chất lượng cao nhất'},
]


def _translate_with_gemini(texts, source_lang, target_lang, api_key, model_id=None):
    """
    Translate a list of subtitle texts using Gemini API
    Uses batch translation for efficiency
    """
    import google.generativeai as genai
    
    genai.configure(api_key=api_key)
    
    source_name = SUPPORTED_LANGUAGES.get(source_lang, source_lang)
    target_name = SUPPORTED_LANGUAGES.get(target_lang, target_lang)
    
    use_model = model_id or DEFAULT_GEMINI_MODEL
    
    # Batch texts into groups of ~50 to avoid too-long prompts
    BATCH_SIZE = 50
    all_translated = []
    
    for batch_start in range(0, len(texts), BATCH_SIZE):
        batch = texts[batch_start:batch_start + BATCH_SIZE]
        
        # Create numbered list for batch translation
        numbered_texts = '\n'.join(f'[{i+1}] {t}' for i, t in enumerate(batch))
        
        prompt = f"""Translate the following subtitle lines from {source_name} to {target_name}.
Keep the exact same numbering format [N]. Return ONLY the translations, one per line with the same [N] format.
Do NOT add any explanation or extra text. Keep translations natural and concise for subtitles.

{numbered_texts}"""
        
        try:
            model = genai.GenerativeModel(use_model)
            response = model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Parse response - extract translated lines
            translated_batch = []
            for line in result_text.split('\n'):
                line = line.strip()
                if line.startswith('[') and ']' in line:
                    # Extract text after [N]
                    text = line[line.index(']') + 1:].strip()
                    translated_batch.append(text)
                elif line and not line.startswith('#'):
                    translated_batch.append(line)
            
            # If parsing failed, fall back to line-by-line
            if len(translated_batch) != len(batch):
                logger.warning(
                    f"Gemini batch translation mismatch: expected {len(batch)}, "
                    f"got {len(translated_batch)}. Using fallback."
                )
                # Pad or trim to match
                while len(translated_batch) < len(batch):
                    translated_batch.append(batch[len(translated_batch)])
                translated_batch = translated_batch[:len(batch)]
            
            all_translated.extend(translated_batch)
            
        except Exception as e:
            logger.error(f"Gemini translation error: {e}")
            # Fallback: return original texts for this batch
            all_translated.extend(batch)
    
    return all_translated


@csrf_exempt
@require_POST
def translate_subtitle(request):
    """
    Translate subtitle content using Gemini API
    
    POST /media-stream/translate/
    Body (JSON):
      - subtitle_id: int (ID of MediaSubtitle to translate)
      - target_lang: str (target language code: vi, en, de, fr, ja, ko, zh)
      
    OR:
      - vtt_content: str (raw VTT text to translate)
      - source_lang: str (source language code)
      - target_lang: str (target language code)
    
    Response:
      - translated_vtt: str (translated VTT content)
      - source_lang: str
      - target_lang: str
      - cached: bool
    """
    # Parse request body
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)
    
    # Get Gemini API key: ưu tiên key do người dùng gửi từ frontend
    user_api_key = body.get('gemini_api_key', '').strip()
    api_key = user_api_key or _get_gemini_api_key()
    if not api_key:
        return JsonResponse({
            'error': 'Chưa có Gemini API Key. '
                     'Vui lòng nhập API Key trong phần "Dịch AI" để sử dụng tính năng dịch phụ đề.'
        }, status=503)
    
    target_lang = body.get('target_lang', '').strip()
    if not target_lang or target_lang not in SUPPORTED_LANGUAGES:
        return JsonResponse({
            'error': f'Invalid target_lang. Supported: {", ".join(SUPPORTED_LANGUAGES.keys())}'
        }, status=400)
    
    # Mode 1: Translate a subtitle by ID
    subtitle_id = body.get('subtitle_id')
    if subtitle_id:
        try:
            from .models import MediaSubtitle
            subtitle = MediaSubtitle.objects.select_related('media').get(id=subtitle_id)
            source_lang = subtitle.language
            
            # Read VTT content from file
            try:
                subtitle.file.open('r')
                vtt_content = subtitle.file.read()
                subtitle.file.close()
                if isinstance(vtt_content, bytes):
                    vtt_content = vtt_content.decode('utf-8')
            except Exception as e:
                return JsonResponse({'error': f'Cannot read subtitle file: {e}'}, status=500)
                
        except MediaSubtitle.DoesNotExist:
            return JsonResponse({'error': 'Subtitle not found'}, status=404)
    else:
        # Mode 2: Translate raw VTT content
        vtt_content = body.get('vtt_content', '').strip()
        source_lang = body.get('source_lang', '').strip()
        
        if not vtt_content:
            return JsonResponse({'error': 'subtitle_id or vtt_content required'}, status=400)
        if not source_lang:
            return JsonResponse({'error': 'source_lang required when using vtt_content'}, status=400)
    
    # Same language = no translation needed
    if source_lang == target_lang:
        return JsonResponse({
            'translated_vtt': vtt_content,
            'source_lang': source_lang,
            'target_lang': target_lang,
            'cached': True,
        })
    
    # Check cache
    cache_key = f"sub_translate:{hashlib.md5(vtt_content.encode()).hexdigest()}:{target_lang}"
    cached_result = cache.get(cache_key)
    if cached_result:
        return JsonResponse({
            'translated_vtt': cached_result,
            'source_lang': source_lang,
            'target_lang': target_lang,
            'cached': True,
        })
    
    # Parse VTT
    segments = _parse_vtt_content(vtt_content)
    if not segments:
        return JsonResponse({'error': 'No subtitle segments found in VTT'}, status=400)
    
    # Extract texts for translation
    texts = [seg['text'] for seg in segments]
    
    # Translate using Gemini
    gemini_model = body.get('gemini_model', '').strip() or None
    try:
        translated_texts = _translate_with_gemini(texts, source_lang, target_lang, api_key, gemini_model)
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        return JsonResponse({'error': f'Translation failed: {str(e)}'}, status=500)
    
    # Rebuild VTT with translated texts
    for seg, translated in zip(segments, translated_texts):
        seg['text'] = translated
    
    translated_vtt = _rebuild_vtt(segments)
    
    # Cache translation
    cache.set(cache_key, translated_vtt, TRANSLATION_CACHE_TIMEOUT)
    
    return JsonResponse({
        'translated_vtt': translated_vtt,
        'source_lang': source_lang,
        'target_lang': target_lang,
        'cached': False,
        'segment_count': len(segments),
    })


@csrf_exempt
def gemini_models_list(request):
    """
    GET  /media-stream/gemini-models/ — Trả về danh sách models đã cache (cho mọi user)
    POST /media-stream/gemini-models/ — Tải models mới từ Google API bằng API key, cache lên server
    
    Body POST: { gemini_api_key: string }
    """
    if request.method == 'POST':
        # Refresh models from Google API
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        user_key = body.get('gemini_api_key', '').strip()
        api_key = user_key or _get_gemini_api_key()
        if not api_key:
            return JsonResponse({'error': 'Cần API Key để tải danh sách models'}, status=400)
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            models_list = []
            for m in genai.list_models():
                # Only include models that support generateContent (text generation)
                supported = [method.name if hasattr(method, 'name') else str(method) 
                            for method in (m.supported_generation_methods or [])]
                if 'generateContent' not in supported:
                    continue
                
                model_id = m.name.replace('models/', '') if m.name.startswith('models/') else m.name
                display_name = m.display_name or model_id
                desc = m.description or ''
                # Truncate long descriptions
                if len(desc) > 80:
                    desc = desc[:77] + '...'
                
                models_list.append({
                    'id': model_id,
                    'name': display_name,
                    'description': desc,
                })
            
            if not models_list:
                return JsonResponse({'error': 'Không tìm thấy model nào hỗ trợ generateContent'}, status=404)
            
            # Sort: stable/flash first, then pro, then others
            def sort_key(m):
                mid = m['id'].lower()
                if '2.5-flash-lite' in mid:
                    return (0, 2, mid)
                if '2.5-flash' in mid and 'preview' not in mid and 'lite' not in mid:
                    return (0, 0, mid)
                if '2.5-flash' in mid:
                    return (0, 1, mid)
                if '2.5-pro' in mid and 'preview' not in mid:
                    return (1, 0, mid)
                if '2.5-pro' in mid:
                    return (1, 1, mid)
                if '3' in mid and 'flash' in mid:
                    return (2, 0, mid)
                if '3' in mid and 'pro' in mid:
                    return (2, 1, mid)
                return (9, 0, mid)
            
            models_list.sort(key=sort_key)
            
            # Cache for all users
            cache.set(GEMINI_MODELS_CACHE_KEY, models_list, GEMINI_MODELS_CACHE_TIMEOUT)
            
            logger.info(f"Refreshed Gemini models list: {len(models_list)} models cached")
            
            return JsonResponse({
                'models': models_list,
                'default': DEFAULT_GEMINI_MODEL,
                'refreshed': True,
                'count': len(models_list),
            })
            
        except Exception as e:
            logger.error(f"Failed to fetch Gemini models: {e}")
            return JsonResponse({'error': f'Lỗi tải models: {str(e)}'}, status=500)
    
    # GET — Return cached or fallback
    cached_models = cache.get(GEMINI_MODELS_CACHE_KEY)
    return JsonResponse({
        'models': cached_models or GEMINI_MODELS_FALLBACK,
        'default': DEFAULT_GEMINI_MODEL,
        'cached': cached_models is not None,
    })


@csrf_exempt
@require_POST
def word_lookup(request):
    """
    POST /media-stream/word-lookup/
    Look up word/phrase meaning using Gemini API
    
    Body: { word, context, source_lang, target_lang, gemini_api_key?, gemini_model? }
    """
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    word = body.get('word', '').strip()
    context = body.get('context', '').strip()
    source_lang = body.get('source_lang', '').strip()
    target_lang = body.get('target_lang', 'vi').strip()
    
    if not word:
        return JsonResponse({'error': 'word required'}, status=400)
    
    # API key
    user_key = body.get('gemini_api_key', '').strip()
    api_key = user_key or _get_gemini_api_key()
    if not api_key:
        return JsonResponse({'error': 'Gemini API Key required'}, status=503)
    
    # Cache
    cache_key = f"word_lookup:{hashlib.md5(f'{word}:{context}:{source_lang}:{target_lang}'.encode()).hexdigest()}"
    cached = cache.get(cache_key)
    if cached:
        return JsonResponse(cached)
    
    source_name = SUPPORTED_LANGUAGES.get(source_lang, source_lang or 'auto-detect')
    target_name = SUPPORTED_LANGUAGES.get(target_lang, target_lang)
    
    model_id = body.get('gemini_model', '').strip() or DEFAULT_GEMINI_MODEL
    
    prompt = f"""You are a language learning dictionary. The user is hovering over a word/phrase while watching a video with subtitles.

Word/Phrase: "{word}"
{f'Sentence context: "{context}"' if context else ''}
Source language: {source_name}
Translate to: {target_name}

Respond in this EXACT JSON format only (no markdown, no code block):
{{"meaning": "primary translation", "pronunciation": "IPA or phonetic", "word_type": "noun/verb/adj/etc", "examples": ["example 1"]}}

Keep it SHORT - this is a tooltip popup. The meaning should be in {target_name}. Give max 1 short example."""

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_id)
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Strip markdown code block if present
        if text.startswith('```'):
            text = text.split('\n', 1)[1] if '\n' in text else text[3:]
            if text.endswith('```'):
                text = text[:-3]
            text = text.strip()
        
        result = json.loads(text)
        result['word'] = word
        result['cached'] = False
        
        # Cache for 24h
        cache.set(cache_key, result, 60 * 60 * 24)
        
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        # Gemini didn't return valid JSON, return raw meaning
        return JsonResponse({
            'word': word,
            'meaning': response.text.strip()[:200] if response else 'Không tra được',
            'cached': False,
        })
    except Exception as e:
        logger.error(f"Word lookup error: {e}")
        return JsonResponse({'error': str(e)}, status=500)
