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
        logger.warning("YOUTUBE_API_KEY chưa được cấu hình trong settings")
        return _fetch_youtube_info_noembed(video_id)
    
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
            'thumbnail': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
            'view_count': int(statistics.get('viewCount', 0)),
            'channel_title': snippet.get('channelTitle', ''),
            'published_at': snippet.get('publishedAt', ''),
            'tags': snippet.get('tags', []),
        }
        
    except ImportError:
        logger.error("Không thể import googleapiclient. Hãy cài đặt: pip install google-api-python-client")
        return _fetch_youtube_info_noembed(video_id)
    except HttpError as e:
        logger.error(f"YouTube API error: {e}")
        return _fetch_youtube_info_noembed(video_id)
    except Exception as e:
        logger.error(f"Lỗi khi lấy thông tin YouTube: {e}")
        return _fetch_youtube_info_noembed(video_id)


def _fetch_youtube_info_noembed(video_id: str) -> Optional[Dict[str, Any]]:
    """
    Phương án dự phòng: Lấy thông tin cơ bản từ noembed.com (không cần API key)
    Chỉ lấy được title, không có description đầy đủ
    """
    try:
        import requests
        
        url = f"https://noembed.com/embed?url=https://www.youtube.com/watch?v={video_id}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'title' in data:
                return {
                    'title': data.get('title', ''),
                    'description': '',  # noembed không cung cấp description
                    'duration': '',
                    'thumbnail': data.get('thumbnail_url', f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"),
                    'view_count': 0,
                    'channel_title': data.get('author_name', ''),
                    'published_at': '',
                    'tags': [],
                }
        return None
    except Exception as e:
        logger.error(f"Lỗi khi lấy thông tin từ noembed: {e}")
        return None
