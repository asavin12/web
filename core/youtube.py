"""
YouTube API Utilities
Tự động lấy thông tin video từ YouTube
"""
import re
import logging
from typing import Optional, Dict, Any

from django.conf import settings

logger = logging.getLogger(__name__)


def extract_youtube_id(url_or_id: str) -> str:
    """
    Trích xuất YouTube Video ID từ nhiều định dạng:
    - ID thuần: dQw4w9WgXcQ
    - youtu.be: https://youtu.be/dQw4w9WgXcQ?si=abc123
    - youtube.com: https://www.youtube.com/watch?v=dQw4w9WgXcQ
    - youtube.com với time: https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=143s
    - youtube.com/embed: https://www.youtube.com/embed/dQw4w9WgXcQ
    """
    if not url_or_id:
        return ''
    
    url_or_id = url_or_id.strip()
    
    # Nếu đã là ID thuần (11 ký tự alphanumeric + - _)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
        return url_or_id
    
    # Pattern cho youtu.be/VIDEO_ID
    match = re.search(r'youtu\.be/([a-zA-Z0-9_-]{11})', url_or_id)
    if match:
        return match.group(1)
    
    # Pattern cho youtube.com/watch?v=VIDEO_ID
    match = re.search(r'youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})', url_or_id)
    if match:
        return match.group(1)
    
    # Pattern cho youtube.com/embed/VIDEO_ID
    match = re.search(r'youtube\.com/embed/([a-zA-Z0-9_-]{11})', url_or_id)
    if match:
        return match.group(1)
    
    # Pattern cho youtube.com/v/VIDEO_ID
    match = re.search(r'youtube\.com/v/([a-zA-Z0-9_-]{11})', url_or_id)
    if match:
        return match.group(1)
    
    # Nếu không match được, trả về nguyên bản
    return url_or_id


def parse_duration(duration: str) -> str:
    """
    Chuyển đổi ISO 8601 duration sang định dạng đọc được
    Ví dụ: PT1H23M45S -> 1:23:45, PT5M30S -> 5:30
    """
    if not duration:
        return ''
    
    # Regex để parse ISO 8601 duration
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
    if not match:
        return duration
    
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"


def fetch_youtube_info(video_id: str) -> Optional[Dict[str, Any]]:
    """
    Lấy thông tin video từ YouTube Data API v3
    
    Returns:
        Dict với các key: title, description, duration, thumbnail, view_count, channel_title
        Hoặc None nếu không lấy được
    """
    api_key = getattr(settings, 'YOUTUBE_API_KEY', None)
    
    if not api_key:
        logger.info("YOUTUBE_API_KEY chưa cấu hình, dùng page scraper")
        # Try page scraper first (fast, no deps), then yt-dlp as backup
        result = _fetch_youtube_info_noembed(video_id)
        if result and result.get('duration_seconds'):
            return result
        logger.info("Page scraper thiếu data, thử yt-dlp...")
        return _fetch_youtube_info_ytdlp(video_id) or result
    
    try:
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
        
        youtube = build('youtube', 'v3', developerKey=api_key)
        
        # Gọi API để lấy thông tin video
        request = youtube.videos().list(
            part='snippet,contentDetails,statistics',
            id=video_id
        )
        response = request.execute()
        
        if not response.get('items'):
            logger.warning(f"Không tìm thấy video với ID: {video_id}")
            return None
        
        item = response['items'][0]
        snippet = item.get('snippet', {})
        content_details = item.get('contentDetails', {})
        statistics = item.get('statistics', {})
        
        return {
            'title': snippet.get('title', ''),
            'description': snippet.get('description', ''),
            'duration': parse_duration(content_details.get('duration', '')),
            'duration_seconds': _parse_duration_seconds(content_details.get('duration', '')),
            'thumbnail': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
            'view_count': int(statistics.get('viewCount', 0)),
            'channel_title': snippet.get('channelTitle', ''),
            'published_at': snippet.get('publishedAt', ''),
            'tags': snippet.get('tags', []),
        }
        
    except ImportError:
        logger.error("Không thể import googleapiclient, dùng yt-dlp fallback")
        return _fetch_youtube_info_ytdlp(video_id)
    except HttpError as e:
        logger.error(f"YouTube API error: {e}, dùng yt-dlp fallback")
        return _fetch_youtube_info_ytdlp(video_id)
    except Exception as e:
        logger.error(f"Lỗi khi lấy thông tin YouTube: {e}")
        return _fetch_youtube_info_ytdlp(video_id)


def _parse_duration_seconds(duration: str) -> Optional[int]:
    """Parse ISO 8601 duration to seconds"""
    if not duration:
        return None
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
    if not match:
        return None
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


def _fetch_youtube_info_ytdlp(video_id: str) -> Optional[Dict[str, Any]]:
    """
    Lấy thông tin YouTube bằng yt-dlp (không cần API key).
    Trả về đầy đủ: title, description, duration, thumbnail, tags...
    """
    try:
        import yt_dlp
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'socket_timeout': 15,
        }
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        
        if not info:
            logger.warning(f"yt-dlp: không lấy được info cho {video_id}")
            return _fetch_youtube_info_noembed(video_id)
        
        duration_secs = info.get('duration') or 0
        if duration_secs:
            hours, remainder = divmod(int(duration_secs), 3600)
            minutes, seconds = divmod(remainder, 60)
            duration_str = f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes}:{seconds:02d}"
        else:
            duration_str = ''
        
        return {
            'title': info.get('title', ''),
            'description': info.get('description', ''),
            'duration': duration_str,
            'duration_seconds': int(duration_secs) if duration_secs else None,
            'thumbnail': info.get('thumbnail', f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"),
            'view_count': info.get('view_count', 0) or 0,
            'channel_title': info.get('uploader', '') or info.get('channel', ''),
            'published_at': info.get('upload_date', ''),
            'tags': info.get('tags', []) or [],
        }
    except ImportError:
        logger.error("yt-dlp chưa cài đặt: pip install yt-dlp")
        return _fetch_youtube_info_noembed(video_id)
    except Exception as e:
        logger.error(f"yt-dlp error cho {video_id}: {e}")
        return _fetch_youtube_info_noembed(video_id)


def _fetch_youtube_info_noembed(video_id: str) -> Optional[Dict[str, Any]]:
    """
    Phương án dự phòng cuối: lấy thông tin từ YouTube page trực tiếp.
    Parse JSON-LD và ytInitialPlayerResponse từ HTML page.
    Không cần API key, không cần yt-dlp.
    """
    import requests
    import json
    
    result = {
        'title': '',
        'description': '',
        'duration': '',
        'duration_seconds': None,
        'thumbnail': f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
        'view_count': 0,
        'channel_title': '',
        'published_at': '',
        'tags': [],
    }
    
    # Strategy 1: noembed for basic title/thumbnail
    try:
        url = f"https://noembed.com/embed?url=https://www.youtube.com/watch?v={video_id}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            result['title'] = data.get('title', '')
            result['channel_title'] = data.get('author_name', '')
            if data.get('thumbnail_url'):
                result['thumbnail'] = data['thumbnail_url']
    except Exception as e:
        logger.debug(f"noembed failed: {e}")
    
    # Strategy 2: Parse YouTube page for duration + detailed info
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        page_url = f"https://www.youtube.com/watch?v={video_id}"
        resp = requests.get(page_url, headers=headers, timeout=15)
        
        if resp.status_code == 200:
            html = resp.text
            
            # Extract from ytInitialPlayerResponse
            match = re.search(r'var ytInitialPlayerResponse\s*=\s*(\{.+?\});\s*(?:var|</script>)', html)
            if match:
                try:
                    player_data = json.loads(match.group(1))
                    video_details = player_data.get('videoDetails', {})
                    
                    if video_details.get('lengthSeconds'):
                        secs = int(video_details['lengthSeconds'])
                        result['duration_seconds'] = secs
                        hours, remainder = divmod(secs, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        result['duration'] = f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes}:{seconds:02d}"
                    
                    if not result['title'] and video_details.get('title'):
                        result['title'] = video_details['title']
                    
                    if video_details.get('shortDescription'):
                        result['description'] = video_details['shortDescription']
                    
                    if video_details.get('viewCount'):
                        result['view_count'] = int(video_details['viewCount'])
                    
                    if video_details.get('author'):
                        result['channel_title'] = video_details['author']
                    
                    if video_details.get('keywords'):
                        result['tags'] = video_details['keywords'][:10]
                    
                    logger.info(f"YouTube page parse OK for {video_id}: duration={result['duration']}")
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    logger.debug(f"ytInitialPlayerResponse parse error: {e}")
            
            # Fallback: extract from meta tags if player response failed
            if not result['duration_seconds']:
                dur_match = re.search(r'"lengthSeconds"\s*:\s*"(\d+)"', html)
                if dur_match:
                    secs = int(dur_match.group(1))
                    result['duration_seconds'] = secs
                    hours, remainder = divmod(secs, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    result['duration'] = f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes}:{seconds:02d}"
                    logger.info(f"YouTube meta parse OK for {video_id}: duration={result['duration']}")
    except Exception as e:
        logger.error(f"YouTube page scrape error cho {video_id}: {e}")
    
    # Return result if we got at least a title
    if result['title']:
        return result
    return None
