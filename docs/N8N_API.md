# N8N Automation API Documentation

## Tổng quan

UnstressVN cung cấp API để tích hợp với n8n, cho phép tự động đăng bài viết lên website.

**Base URL:** `https://your-domain.com/api/v1/n8n/`

**Authentication:** Sử dụng API Key trong header `X-API-Key`

## Cấu hình

### 1. Lấy API Key

API Key được cấu hình trong file `.env`:

```bash
N8N_API_KEY=your-secret-api-key-here
```

Để tạo API Key mới:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Cấu hình trong n8n

Trong n8n, tạo HTTP Request node với:

- **Method:** POST
- **URL:** `https://your-domain.com/api/v1/n8n/news/`
- **Headers:**
  - `Content-Type: application/json`
  - `X-API-Key: your-api-key`
- **Body:** JSON

## API Endpoints

### Health Check

Kiểm tra trạng thái API (không cần authentication).

```
GET /api/v1/n8n/health/
```

**Response:**
```json
{
  "status": "ok",
  "service": "UnstressVN API",
  "version": "1.0.0",
  "timestamp": "2026-01-24T07:20:37.024667+00:00"
}
```

---

### Lấy danh sách Categories

```
GET /api/v1/n8n/categories/?type=news|knowledge|resources|all
```

**Headers:**
- `X-API-Key: your-api-key`

**Response:**
```json
{
  "success": true,
  "categories": [
    {"id": 1, "name": "Học tiếng Đức", "slug": "hoc-tieng-duc", "type": "news"},
    {"id": 2, "name": "Ngữ pháp", "slug": "ngu-phap", "type": "knowledge"}
  ]
}
```

---

### Tạo bài viết Tin tức (News)

```
POST /api/v1/n8n/news/
```

**Headers:**
- `Content-Type: application/json`
- `X-API-Key: your-api-key`

**Body:**
```json
{
  "title": "Tiêu đề bài viết (bắt buộc)",
  "content": "Nội dung HTML của bài viết (bắt buộc)",
  "excerpt": "Mô tả ngắn (tùy chọn)",
  "category": "slug-category hoặc id (tùy chọn)",
  "is_featured": false,
  "is_published": true,
  "meta_title": "SEO title (tùy chọn)",
  "meta_description": "SEO description (tùy chọn)",
  "meta_keywords": "keyword1, keyword2 (tùy chọn)"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "article": {
    "id": 10,
    "title": "Tiêu đề bài viết",
    "slug": "tieu-de-bai-viet",
    "url": "/tin-tuc/tieu-de-bai-viet",
    "is_published": true,
    "created_at": "2026-01-24T07:20:44.871215+00:00"
  },
  "message": "Đã tạo bài viết tin tức thành công"
}
```

---

### Tạo bài viết Kiến thức (Knowledge)

```
POST /api/v1/n8n/knowledge/
```

**Headers:**
- `Content-Type: application/json`
- `X-API-Key: your-api-key`

**Body:**
```json
{
  "title": "Tiêu đề bài viết (bắt buộc)",
  "content": "Nội dung HTML của bài viết (bắt buộc)",
  "excerpt": "Mô tả ngắn (tùy chọn)",
  "category": "slug-category hoặc id (tùy chọn)",
  "language": "de/en/all (mặc định: all)",
  "level": "A1/A2/B1/B2/C1/C2/all (mặc định: all)",
  "is_published": true,
  "meta_title": "SEO title (tùy chọn)",
  "meta_description": "SEO description (tùy chọn)",
  "meta_keywords": "keyword1, keyword2 (tùy chọn)"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "article": {
    "id": 13,
    "title": "Học từ vựng tiếng Đức với flashcards",
    "slug": "hoc-tu-vung-tieng-duc-voi-flashcards",
    "language": "de",
    "level": "A1",
    "url": "/kien-thuc/hoc-tu-vung-tieng-duc-voi-flashcards",
    "is_published": true,
    "created_at": "2026-01-24T07:20:51.540412+00:00"
  },
  "message": "Đã tạo bài viết kiến thức thành công"
}
```

---

### Tạo Tài liệu (Resource)

```
POST /api/v1/n8n/resources/
```

**Headers:**
- `Content-Type: application/json`
- `X-API-Key: your-api-key`

**Body:**
```json
{
  "title": "Tên tài liệu (bắt buộc)",
  "description": "Mô tả tài liệu (bắt buộc)",
  "category": "slug-category hoặc id (tùy chọn)",
  "resource_type": "ebook/pdf/audio/video/document/flashcard",
  "external_url": "https://drive.google.com/...",
  "youtube_url": "https://youtube.com/... (cho video)",
  "author": "Tác giả (tùy chọn)",
  "is_featured": false
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "resource": {
    "id": 25,
    "title": "Tên tài liệu",
    "slug": "ten-tai-lieu",
    "resource_type": "pdf",
    "url": "/tai-lieu/ten-tai-lieu",
    "created_at": "2026-01-24T07:25:00.000000+00:00"
  },
  "message": "Đã tạo tài liệu thành công"
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "success": false,
  "error": "Thiếu trường \"title\""
}
```

### 401 Unauthorized
```json
{
  "detail": "API Key không hợp lệ"
}
```

---

## Ví dụ n8n Workflow

### Workflow tự động đăng bài từ RSS

1. **RSS Feed Trigger**: Theo dõi RSS feed
2. **Set**: Xử lý dữ liệu
3. **HTTP Request**: POST đến API
   - URL: `https://unstressvn.com/api/v1/n8n/news/`
   - Headers: `X-API-Key: {{$credentials.unstressvn_api_key}}`
   - Body:
     ```json
     {
       "title": "{{$json.title}}",
       "content": "{{$json.content}}",
       "excerpt": "{{$json.description}}",
       "category": "tin-tuc-tong-hop",
       "is_published": true
     }
     ```

### Workflow tự động đăng từ Google Sheets

1. **Google Sheets Trigger**: Khi có dòng mới
2. **HTTP Request**: POST đến API
   - Body mapping từ Google Sheets columns

---

## Lưu ý bảo mật

1. **KHÔNG** share API Key công khai
2. Sử dụng HTTPS trong production
3. Thay đổi API Key định kỳ
4. Giám sát access logs
5. Thiết lập rate limiting trong production

---

## Contact

- **Email:** unstressvn@gmail.com
- **Website:** https://unstressvn.com
