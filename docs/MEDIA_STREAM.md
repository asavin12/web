# MediaStream - Hệ thống Streaming Media với Bảo vệ Referrer

## Giới thiệu

MediaStream là một Django app cho phép upload và stream video/audio với bảo vệ referrer. Link stream chỉ hoạt động khi được truy cập từ domain unstressvn.com.

**Hỗ trợ 2 loại storage:**
- **Local Storage**: Upload trực tiếp lên server
- **MinIO/S3**: Upload lên MinIO trên Coolify (khuyến nghị cho production)

## Tính năng

### ✅ Upload & Quản lý Media
- Upload video (MP4, WebM, OGG, AVI, MOV, FLV)
- Upload audio (MP3, WAV, OGG, FLAC, AAC)
- Drag & drop upload interface
- Quản lý qua Django Admin
- Tự động generate thumbnail cho video
- **Hỗ trợ MinIO/S3 storage** để tránh quá tải server

### ✅ Streaming với Referrer Protection
- Chỉ cho phép truy cập từ domain được cấu hình
- Hỗ trợ HTTP Range requests (seeking video/audio)
- Trả về 404 cho các request không hợp lệ (ẩn sự tồn tại của file)

### ✅ Phụ đề & Đa ngôn ngữ
- Hỗ trợ subtitle VTT/SRT
- Đa ngôn ngữ: Tiếng Việt, Anh, Trung, Nhật, Hàn, Pháp, Đức
- Phân loại theo level: Beginner → Native

### ✅ REST API
- Full REST API với Django REST Framework
- Filter theo media_type, language, level, category
- Search, pagination, ordering
- Public API cho frontend

## Cấu trúc thư mục

```
mediastream/
├── __init__.py
├── admin.py          # Django Admin configuration
├── api_views.py      # REST API ViewSets
├── apps.py           # App configuration
├── models.py         # Database models
├── serializers.py    # DRF Serializers
├── urls.py           # URL routing
├── views.py          # Streaming views với referrer protection
└── migrations/
```

## URLs

### Streaming (Protected)
| URL | Method | Description |
|-----|--------|-------------|
| `/media-stream/play/<uid>/` | GET | Stream video/audio |
| `/media-stream/download/<uid>/` | GET | Download file |
| `/media-stream/subtitle/<id>/` | GET | Get subtitle file |

### REST API
| URL | Method | Description |
|-----|--------|-------------|
| `/media-stream/api/media/` | GET | List all media |
| `/media-stream/api/media/<uid>/` | GET | Get media detail |
| `/media-stream/api/media/featured/` | GET | Featured media |
| `/media-stream/api/media/recent/` | GET | Recent media |
| `/media-stream/api/categories/` | GET | List categories |
| `/media-stream/api/playlists/` | GET | List playlists |

### Admin
| URL | Method | Description |
|-----|--------|-------------|
| `/media-stream/admin/upload/` | GET | Upload page |
| `/media-stream/admin/upload/api/` | POST | Upload API |
| `/media-stream/admin/manage/` | GET | Manage page |
| `/media-stream/admin/delete/<uid>/` | POST | Delete media |

## Cấu hình MinIO trên Coolify

### 1. Tạo MinIO Service trên Coolify

1. Vào Coolify Dashboard → Services → Add New
2. Chọn MinIO từ danh sách
3. Configure:
   - **Root User**: `minio_admin` (hoặc tên khác)
   - **Root Password**: Password mạnh
   - **Domain**: Thêm domain cho MinIO Console (vd: `minio.unstressvn.com`)

### 2. Tạo Bucket cho MediaStream

1. Truy cập MinIO Console: `https://minio.unstressvn.com`
2. Login với Root User/Password
3. Tạo bucket mới tên `mediastream`
4. (Optional) Tạo Access Key riêng cho Django

### 3. Cấu hình Environment Variables

Thêm vào file `.env` hoặc Environment Variables trên Coolify:

```env
# MinIO Configuration
MINIO_ENDPOINT_URL=https://minio.unstressvn.com
MINIO_ACCESS_KEY=your_access_key
MINIO_SECRET_KEY=your_secret_key
MINIO_MEDIA_BUCKET=mediastream
MINIO_REGION=us-east-1
```

### 4. Kiểm tra kết nối

```python
# Trong Django shell
from django.conf import settings
print(f"MinIO URL: {settings.MINIO_ENDPOINT_URL}")
print(f"Bucket: {settings.MINIO_MEDIA_BUCKET}")

# Test upload
from mediastream.models import StreamMedia
media = StreamMedia.objects.first()
if media:
    print(f"Storage: {media.file.storage.__class__.__name__}")
```

## Cấu hình Referrer Protection

Trong `views.py`:

```python
# Các domain được phép truy cập
ALLOWED_DOMAINS = [
    'unstressvn.com',
    'www.unstressvn.com',
    'localhost',
    '127.0.0.1',
]

# Có cho phép direct access không (không có referrer)
ALLOW_DIRECT_ACCESS = False

# Check referrer trong DEBUG mode
CHECK_REFERRER_IN_DEBUG = False  # Bypass trong development
```

## Sử dụng trong Frontend

### React Components

```tsx
import { VideoPlayer, AudioPlayer, MediaGrid, useMediaList } from '@/components/common/MediaStream';

// Video Player
<VideoPlayer 
  media={mediaItem}
  autoPlay={false}
  showControls={true}
  onEnded={() => console.log('Video ended')}
/>

// Audio Player
<AudioPlayer 
  media={mediaItem}
  autoPlay={false}
/>

// Media Grid
<MediaGrid 
  items={mediaItems}
  onSelect={(item) => setSelectedMedia(item)}
  columns={3}
/>

// Hook để fetch media
const { items, loading, error } = useMediaList({
  mediaType: 'video',
  language: 'vi',
  level: 'beginner'
});
```

### Embed Code (HTML)

```html
<!-- Video -->
<video controls>
  <source src="/media-stream/play/550e8400-e29b-41d4-a716-446655440000/" type="video/mp4">
</video>

<!-- Audio -->
<audio controls>
  <source src="/media-stream/play/550e8400-e29b-41d4-a716-446655440000/" type="audio/mpeg">
</audio>

<!-- Video với subtitles -->
<video controls>
  <source src="/media-stream/play/550e8400-e29b-41d4-a716-446655440000/" type="video/mp4">
  <track kind="subtitles" label="Tiếng Việt" srclang="vi" src="/media-stream/subtitle/1/">
  <track kind="subtitles" label="English" srclang="en" src="/media-stream/subtitle/2/">
</video>
```

## API Examples

### Get Media List
```bash
GET /media-stream/api/media/?media_type=video&language=vi&level=beginner

Response:
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "uid": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Học tiếng Việt cơ bản",
      "media_type": "video",
      "language": "vi",
      "level": "beginner",
      "stream_url": "/media-stream/play/550e8400-e29b-41d4-a716-446655440000/",
      "duration_formatted": "05:30",
      "view_count": 100
    }
  ]
}
```

### Get Media Detail
```bash
GET /media-stream/api/media/550e8400-e29b-41d4-a716-446655440000/

Response:
{
  "id": 1,
  "uid": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Học tiếng Việt cơ bản",
  "description": "Video hướng dẫn...",
  "media_type": "video",
  "stream_url": "/media-stream/play/550e8400-e29b-41d4-a716-446655440000/",
  "subtitles": [
    {"id": 1, "language": "vi", "label": "Tiếng Việt", "subtitle_url": "/media-stream/subtitle/1/"},
    {"id": 2, "language": "en", "label": "English", "subtitle_url": "/media-stream/subtitle/2/"}
  ],
  "embed_code": "<video controls>..."
}
```

## Models

### StreamMedia
Mô hình chính cho media files:
- `uid`: UUID unique identifier (dùng cho URLs)
- `title`, `slug`, `description`: Thông tin mô tả
- `file`: FileField cho media file
- `thumbnail`: ImageField cho thumbnail
- `media_type`: 'video' hoặc 'audio'
- `language`: Ngôn ngữ của nội dung
- `level`: Trình độ học tập
- `duration`: Thời lượng (giây)
- `is_active`, `is_public`, `requires_login`: Access control
- `view_count`, `download_count`: Statistics

### MediaCategory
Danh mục phân loại media:
- Hỗ trợ nested categories (parent-child)
- Icon cho mỗi category

### MediaSubtitle
Phụ đề cho media:
- Hỗ trợ nhiều ngôn ngữ
- Format VTT hoặc SRT

### MediaPlaylist
Playlist cho học tập:
- Tập hợp nhiều media items
- Sắp xếp thứ tự qua PlaylistItem

## Security Notes

1. **Referrer Protection**: Link stream chỉ hoạt động khi HTTP Referer header là từ domain được phép. Direct access (paste link vào browser) sẽ trả về 404.

2. **UUID-based URLs**: Sử dụng UUID thay vì ID số để tránh dự đoán URL.

3. **404 thay vì 403**: Khi access bị từ chối, trả về 404 để ẩn sự tồn tại của resource.

4. **Access Control**: Hỗ trợ `requires_login` và `is_public` flags để kiểm soát truy cập chi tiết.

## Development

```bash
# Tạo migrations
python manage.py makemigrations mediastream

# Chạy migrations
python manage.py migrate

# Test
python manage.py test mediastream
```

## Upload via Admin

1. Truy cập `/media-stream/admin/upload/`
2. Login với tài khoản staff
3. Drag & drop file hoặc click để chọn
4. Điền thông tin: Title, Category, Language, Level
5. Click Upload

## Production Deployment

Khi deploy lên production:

1. Cập nhật `ALLOWED_DOMAINS` với domain thực
2. Set `CHECK_REFERRER_IN_DEBUG = True` nếu muốn test referrer protection
3. Set `ALLOW_DIRECT_ACCESS = False` để chặn direct access
4. Configure nginx/apache để handle large file uploads
5. Consider using CDN cho streaming performance
