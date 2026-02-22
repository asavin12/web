# N8N Automation API Documentation

## Tổng quan

API này cho phép n8n workflow tự động tạo nội dung trên website UnstressVN.

## Xác thực

Tất cả các endpoint (trừ `/health/`) đều yêu cầu API Key trong header:

```
X-API-Key: <your-api-key>
```

API Key được lưu trong database và có thể quản lý qua Admin Panel.

---

## Endpoints

### 1. Health Check

Kiểm tra kết nối API (không cần xác thực)

```http
GET /api/v1/n8n/health/
```

**Response:**
```json
{
  "status": "ok",
  "service": "UnstressVN API",
  "version": "1.0.0",
  "timestamp": "2024-01-25T00:00:00Z"
}
```

---

### 2. Get Categories

Lấy danh sách tất cả categories

```http
GET /api/v1/n8n/categories/
```

**Headers:**
```
X-API-Key: <your-api-key>
```

**Response:**
```json
{
  "success": true,
  "categories": [
    {"id": 1, "name": "Học tiếng Đức", "slug": "hoc-tieng-duc", "type": "news"},
    {"id": 1, "name": "Ngữ pháp", "slug": "ngu-phap", "type": "knowledge"},
    {"id": 1, "name": "Tiếng Đức", "slug": "tieng-duc", "type": "resources"}
  ]
}
```

---

### 3. Create News Article

Tạo bài viết tin tức (có hỗ trợ ảnh)

```http
POST /api/v1/n8n/news/
```

**Headers:**
```
X-API-Key: <your-api-key>
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "title": "Tiêu đề bài viết",
  "content": "<p>Nội dung HTML của bài viết</p>",
  "excerpt": "Mô tả ngắn (tùy chọn)",
  "category": "hoc-tieng-duc",
  "cover_image_url": "https://example.com/image.jpg",
  "auto_placeholder": true,
  "is_featured": false,
  "is_published": true,
  "meta_title": "SEO title (tùy chọn)",
  "meta_description": "SEO description (tùy chọn)",
  "meta_keywords": "keyword1, keyword2 (tùy chọn)",
  "source_url": "https://source.com/original-article",
  "source_id": "unique-id-from-source",
  "workflow_id": "n8n-workflow-id",
  "execution_id": "n8n-execution-id",
  "is_ai_generated": true,
  "ai_model": "gpt-4"
}
```

**Required fields:** `title`, `content`

**Image Support:**
| Field | Type | Description |
|-------|------|-------------|
| `cover_image_url` | string | URL ảnh bìa - auto download, convert WebP, tạo responsive sizes |
| `cover_image` | file | Upload ảnh trực tiếp (multipart/form-data) |
| `auto_placeholder` | bool | Default `true` - tự tạo placeholder nếu không có ảnh |

**Image Pipeline:**
1. Ảnh được download từ URL hoặc upload trực tiếp
2. Auto convert sang WebP format (chất lượng cao, tối ưu dung lượng)
3. Auto tạo thumbnail (400x267px)
4. Auto tạo responsive sizes (480w, 768w, 1200w, 1920w) cho srcset
5. Auto copy sang og_image cho social media sharing
6. Nếu không có ảnh → tự tạo placeholder image từ title

**Response:**
```json
{
  "success": true,
  "article": {
    "id": 11,
    "title": "Tiêu đề bài viết",
    "slug": "tieu-de-bai-viet",
    "url": "/tin-tuc/tieu-de-bai-viet",
    "is_published": true,
    "created_at": "2024-01-25T00:00:00Z",
    "cover_image": "/media/news/covers/unstressvn-tieu-de-bai-viet-cover.webp",
    "thumbnail": "/media/news/thumbnails/unstressvn-tieu-de-bai-viet-thumb.webp",
    "has_responsive_images": true
  },
  "image_source": "url",
  "message": "Đã tạo bài viết thành công"
}
```

---

### 4. Create Knowledge Article

Tạo bài viết kiến thức học tập (có hỗ trợ ảnh)

```http
POST /api/v1/n8n/knowledge/
```

**Headers:**
```
X-API-Key: <your-api-key>
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "title": "Ngữ pháp tiếng Đức A1",
  "content": "<p>Nội dung bài học</p>",
  "excerpt": "Mô tả ngắn",
  "category": "ngu-phap",
  "language": "de",
  "level": "A1",
  "cover_image_url": "https://example.com/grammar-image.jpg",
  "auto_placeholder": true,
  "is_published": true,
  "is_ai_generated": true,
  "ai_model": "gpt-4",
  "workflow_id": "workflow-123",
  "execution_id": "exec-456"
}
```

**Required fields:** `title`, `content`

**Language options:** `en` (Tiếng Anh), `de` (Tiếng Đức), `all` (Tất cả)

**Level options:** `A1`, `A2`, `B1`, `B2`, `C1`, `C2`, `all`

**Image Support:** Giống như News Article (xem mục 3)

**Response:**
```json
{
  "success": true,
  "article": {
    "id": 14,
    "title": "Ngữ pháp tiếng Đức A1",
    "slug": "ngu-phap-tieng-duc-a1",
    "language": "de",
    "level": "A1",
    "url": "/kien-thuc/ngu-phap-tieng-duc-a1",
    "is_published": true,
    "created_at": "2024-01-25T00:00:00Z",
    "cover_image": "/media/knowledge/covers/unstressvn-ngu-phap-tieng-duc-a1-cover.webp",
    "thumbnail": "/media/knowledge/thumbnails/unstressvn-ngu-phap-tieng-duc-a1-thumb.webp",
    "has_responsive_images": true
  },
  "image_source": "url",
  "message": "Đã tạo bài viết kiến thức thành công"
}
```

---

### 5. Update News Article

Cập nhật bài viết tin tức (hỗ trợ cập nhật từng phần)

```http
PUT /api/v1/n8n/news/<identifier>/
PATCH /api/v1/n8n/news/<identifier>/
```

**identifier:** Có thể là `slug`, `id`, hoặc `source_id` (N8N tracking)

**Headers:**
```
X-API-Key: <your-api-key>
Content-Type: application/json
```

**Body (JSON) — tất cả trường đều tùy chọn:**
```json
{
  "title": "Tiêu đề mới",
  "content": "<p>Nội dung mới</p>",
  "excerpt": "Mô tả mới",
  "category": "hoc-tieng-duc",
  "is_featured": true,
  "is_published": true,
  "cover_image_url": "https://example.com/new-image.jpg",
  "meta_title": "SEO title mới",
  "meta_description": "SEO description mới",
  "meta_keywords": "keyword1, keyword2",
  "regenerate_slug": false,
  "skip_seo_validation": true,
  "workflow_id": "n8n-workflow-id",
  "execution_id": "n8n-execution-id"
}
```

**Lưu ý:**
- `regenerate_slug`: Nếu `true` và `title` thay đổi → tạo slug mới từ title mới
- `skip_seo_validation`: Default `true` cho update (không bắt buộc SEO check)
- Khi `is_published` chuyển từ `false` → `true` và chưa có `published_at` → tự động set

**Response:**
```json
{
  "success": true,
  "article": {
    "id": 11,
    "title": "Tiêu đề mới",
    "slug": "tieu-de-bai-viet",
    "url": "/tin-tuc/tieu-de-bai-viet",
    "is_published": true,
    "is_featured": true,
    "updated_at": "2024-01-26T10:30:00Z",
    "cover_image": "/media/news/covers/unstressvn-tieu-de-bai-viet-cover.webp"
  },
  "updated_fields": ["title", "content", "is_featured"],
  "image_source": "unchanged",
  "message": "Đã cập nhật bài viết news thành công"
}
```

---

### 6. Update Knowledge Article

Cập nhật bài viết kiến thức (hỗ trợ cập nhật từng phần)

```http
PUT /api/v1/n8n/knowledge/<identifier>/
PATCH /api/v1/n8n/knowledge/<identifier>/
```

**identifier:** Có thể là `slug`, `id`, hoặc `source_id` (N8N tracking)

**Headers:**
```
X-API-Key: <your-api-key>
Content-Type: application/json
```

**Body (JSON) — tất cả trường đều tùy chọn:**
```json
{
  "title": "Tiêu đề mới",
  "content": "<p>Nội dung mới</p>",
  "excerpt": "Mô tả mới",
  "category": "ngu-phap",
  "language": "de",
  "level": "B1",
  "is_featured": true,
  "is_published": true,
  "cover_image_url": "https://example.com/new-image.jpg",
  "meta_title": "SEO title mới",
  "meta_description": "SEO description mới",
  "regenerate_slug": false,
  "skip_seo_validation": true
}
```

**Knowledge-specific fields:**
| Field | Options | Default |
|-------|---------|---------|
| `language` | `de`, `en`, `all` | không thay đổi |
| `level` | `A1`, `A2`, `B1`, `B2`, `C1`, `C2`, `all` | không thay đổi |

**Response:**
```json
{
  "success": true,
  "article": {
    "id": 14,
    "title": "Ngữ pháp tiếng Đức B1",
    "slug": "ngu-phap-tieng-duc-a1",
    "url": "/kien-thuc/ngu-phap-tieng-duc-a1",
    "is_published": true,
    "is_featured": true,
    "updated_at": "2024-01-26T10:30:00Z",
    "cover_image": "/media/knowledge/covers/unstressvn-ngu-phap-tieng-duc-a1-cover.webp"
  },
  "updated_fields": ["title", "level", "is_featured"],
  "image_source": "unchanged",
  "message": "Đã cập nhật bài viết knowledge thành công"
}
```

---

### 7. Create Resource

Tạo tài liệu học tập (ebook, audio, video, pdf...)

```http
POST /api/v1/n8n/resources/
```

**Headers:**
```
X-API-Key: <your-api-key>
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "title": "Ebook Goethe A1",
  "description": "Tài liệu ôn thi Goethe A1 đầy đủ",
  "category": "goethe",
  "language": "de",
  "level": "A1",
  "resource_type": "ebook",
  "external_url": "https://example.com/file.pdf",
  "is_published": true,
  "is_ai_generated": false,
  "workflow_id": "workflow-123"
}
```

**Required fields:** `title`, `description`

**Resource types:** `ebook`, `pdf`, `audio`, `video`, `document`, `other`

**Response:**
```json
{
  "success": true,
  "resource": {
    "id": 25,
    "title": "Ebook Goethe A1",
    "slug": "ebook-goethe-a1",
    "resource_type": "ebook",
    "url": "/tai-lieu/ebook-goethe-a1",
    "created_at": "2024-01-25T00:00:00Z"
  },
  "message": "Đã tạo tài liệu thành công"
}
```

---

### 8. Create Video

Tạo video từ YouTube (auto fetch metadata)

```http
POST /api/v1/n8n/videos/
```

**Headers:**
```
X-API-Key: <your-api-key>
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "youtube_url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "title": "Tiêu đề video (tùy chọn, auto lấy từ YouTube)",
  "description": "Mô tả (tùy chọn)",
  "category": "tieng-duc",
  "language": "de",
  "level": "A1",
  "is_published": true,
  "workflow_id": "workflow-123"
}
```

**Required fields:** `youtube_url`

**Response:**
```json
{
  "success": true,
  "video": {
    "id": 10,
    "title": "Video title",
    "slug": "video-title",
    "youtube_id": "VIDEO_ID",
    "url": "/video/video-title",
    "created_at": "2024-01-25T00:00:00Z"
  },
  "message": "Đã tạo video thành công"
}
```

**Note:** Nếu video đã tồn tại (cùng youtube_id), API sẽ trả về lỗi duplicate.

---

## N8N Tracking Fields

Tất cả các content đều hỗ trợ các fields theo dõi:

| Field | Type | Description |
|-------|------|-------------|
| `source` | string | Nguồn tạo: `manual`, `n8n`, `api`, `rss`, `scraper` |
| `source_url` | string | URL nguồn gốc (nếu import) |
| `source_id` | string | ID từ hệ thống nguồn (để tránh duplicate) |
| `workflow_id` | string | N8N Workflow ID |
| `execution_id` | string | N8N Execution ID |
| `is_ai_generated` | boolean | Content được tạo bởi AI |
| `ai_model` | string | Model AI đã sử dụng (GPT-4, Claude, etc.) |

---

## Error Handling

**401 Unauthorized:**
```json
{
  "detail": "API Key không hợp lệ"
}
```

**400 Bad Request:**
```json
{
  "success": false,
  "error": "Thiếu trường \"title\""
}
```

**409 Conflict (Duplicate):**
```json
{
  "success": false,
  "error": "Video này đã tồn tại",
  "existing_video": {...}
}
```

---

## N8N Workflow Examples

### Example 1: Auto post news from RSS

```javascript
// HTTP Request node
{
  "method": "POST",
  "url": "https://unstressvn.com/api/v1/n8n/news/",
  "headers": {
    "X-API-Key": "your-api-key",
    "Content-Type": "application/json"
  },
  "body": {
    "title": "{{$json.title}}",
    "content": "{{$json.content}}",
    "source_url": "{{$json.link}}",
    "source_id": "{{$json.guid}}",
    "workflow_id": "{{$workflow.id}}",
    "execution_id": "{{$execution.id}}",
    "is_ai_generated": false
  }
}
```

### Example 2: AI-generated content

```javascript
// HTTP Request node (sau khi OpenAI generate content)
{
  "method": "POST",
  "url": "https://unstressvn.com/api/v1/n8n/knowledge/",
  "headers": {
    "X-API-Key": "your-api-key",
    "Content-Type": "application/json"
  },
  "body": {
    "title": "{{$json.title}}",
    "content": "{{$json.ai_content}}",
    "language": "de",
    "level": "A1",
    "category": "ngu-phap",
    "is_ai_generated": true,
    "ai_model": "gpt-4",
    "workflow_id": "{{$workflow.id}}",
    "is_published": false
  }
}
```

---

## API Key Management

API Keys được quản lý qua Django Admin:
- URL: `/admin/core/apikey/`
- Tạo key mới với name `n8n_api_key`
- Có thể tạm ngưng (deactivate) key khi cần

---

## Rate Limits

Hiện tại không có rate limit. Tuy nhiên nên giới hạn:
- Tối đa 100 requests/phút cho automation
- Delay 1-2 giây giữa các requests

---

## Contact

Email: unstressvn@gmail.com
