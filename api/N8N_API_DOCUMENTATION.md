# N8N Automation API Documentation

## Tổng quan

API cho phép n8n workflow tự động tạo, cập nhật, xoá nội dung trên website UnstressVN.
Hỗ trợ đầy đủ 7 loại nội dung: News, Knowledge, Tools, Resources, Videos, Flashcards, Stream Media.

**Base URL:** `https://unstressvn.com/api/v1/n8n/`

## Xác thực

Tất cả endpoint (trừ `/health/`) yêu cầu API Key trong header:

```
X-API-Key: <your-api-key>
```

API Key được lưu trong database, quản lý qua Admin Panel → Core → API Keys.

---

## Tổng quan Endpoints

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/health/` | Health check (không cần auth) |
| **Content Builder** | | |
| POST | `/build-content/` | Chuyển JSON cấu trúc → HTML |
| GET | `/content-schema/` | Lấy danh sách block types + schema |
| **Categories** | | |
| GET | `/categories/?type=` | Danh sách categories |
| POST | `/categories/create/` | Tạo category mới |
| **News** | | |
| POST | `/news/` | Tạo bài tin tức |
| GET | `/news/list/` | Danh sách tin tức |
| PUT/PATCH | `/news/<identifier>/` | Cập nhật tin tức |
| **Knowledge** | | |
| POST | `/knowledge/` | Tạo bài kiến thức |
| GET | `/knowledge/list/` | Danh sách bài kiến thức |
| PUT/PATCH | `/knowledge/<identifier>/` | Cập nhật bài kiến thức |
| **Tools** | | |
| POST | `/tools/` | Tạo công cụ |
| GET | `/tools/list/` | Danh sách công cụ |
| PUT/PATCH | `/tools/<identifier>/` | Cập nhật công cụ |
| **Resources** | | |
| POST | `/resources/` | Tạo tài liệu |
| GET | `/resources/list/` | Danh sách tài liệu |
| PUT/PATCH | `/resources/<identifier>/` | Cập nhật tài liệu |
| **Videos** | | |
| POST | `/videos/` | Tạo video YouTube |
| GET | `/videos/list/` | Danh sách video |
| **Flashcards** | | |
| POST | `/flashcards/` | Tạo bộ flashcard + thẻ |
| PUT/PATCH | `/flashcards/<identifier>/` | Cập nhật bộ flashcard |
| **Stream Media** | | |
| POST | `/stream-media/` | Tạo video GDrive stream |
| **Delete** | | |
| DELETE | `/<type>/<identifier>/delete/` | Xoá nội dung (soft/hard) |
| **Bulk** | | |
| POST | `/bulk/` | Tạo hàng loạt (max 50) |

---

## 1. Health Check

```http
GET /api/v1/n8n/health/
```

Không cần xác thực.

```json
{
  "status": "ok",
  "service": "UnstressVN API",
  "version": "1.0.0",
  "timestamp": "2026-02-25T12:00:00Z"
}
```

---

## 2. Content Builder

Cho phép n8n/AI gửi dữ liệu JSON cấu trúc → tự động sinh HTML chuẩn SEO.

> Chi tiết đầy đủ: `docs/CONTENT_BUILDER_SCHEMA.md`

### 2.1 Build Content (Preview)

```http
POST /api/v1/n8n/build-content/
Content-Type: application/json
```

```json
{
  "lead": "<p>Đoạn mở đầu</p>",
  "toc": true,
  "blocks": [
    {"type": "heading", "level": 2, "text": "Tiêu đề mục"},
    {"type": "paragraph", "text": "Nội dung đoạn văn..."},
    {"type": "table", "headers": ["A", "B"], "rows": [["1", "2"]]}
  ],
  "conclusion": "<p>Kết luận</p>"
}
```

**Response:**
```json
{
  "success": true,
  "html": "<article>...</article>",
  "stats": {
    "word_count": 500,
    "heading_count": 3,
    "table_count": 1,
    "list_count": 0,
    "has_toc": true,
    "has_conclusion": true
  }
}
```

### 2.2 Content Schema

```http
GET /api/v1/n8n/content-schema/
```

Trả về tất cả block types (paragraph, heading, table, info_table, comparison_table, list, blockquote, image, video, code, faq, divider, callout, html) cùng schema mẫu.

### 2.3 Sử dụng với tạo bài viết

Gửi `structured_content` thay vì `content` khi tạo bài News/Knowledge:

```json
{
  "title": "Tiêu đề bài viết",
  "structured_content": {
    "lead": "...",
    "toc": true,
    "blocks": [...],
    "conclusion": "..."
  },
  "category": "hoc-tieng-duc",
  "is_published": true,
  "skip_seo_validation": true
}
```

Response sẽ thêm `content_build_stats` với thống kê nội dung.

---

## 3. Categories

### 3.1 Danh sách categories

```http
GET /api/v1/n8n/categories/?type=news|knowledge|resources|tools|media|all
```

**Response:**
```json
{
  "success": true,
  "categories": [
    {"id": 1, "name": "Học tiếng Đức", "slug": "hoc-tieng-duc", "type": "news"},
    {"id": 1, "name": "Ngữ pháp", "slug": "ngu-phap", "type": "knowledge"}
  ]
}
```

### 2.2 Tạo category mới

```http
POST /api/v1/n8n/categories/create/
Content-Type: application/json
```

| Field | Bắt buộc | Mô tả |
|-------|----------|-------|
| `type` | ✅ | `news`, `knowledge`, `resources`, `tools`, `media` |
| `name` | ✅ | Tên category |
| `slug` | | Auto-generate từ name nếu bỏ qua |
| `description` | | Mô tả |
| `icon` | | Emoji hoặc lucide-react icon name |

**Response (201):**
```json
{
  "success": true,
  "category": {"id": 5, "name": "Phim Đức", "slug": "phim-duc", "type": "media"},
  "message": "Đã tạo category media thành công",
  "action": "created"
}
```

Auto skip nếu slug đã tồn tại (trả 200 + `action: "skipped"`).

---

## 3. News — Tin tức

### 3.1 Tạo bài viết

```http
POST /api/v1/n8n/news/
Content-Type: application/json
```

| Field | Bắt buộc | Mô tả |
|-------|----------|-------|
| `title` | ✅ | Tiêu đề (40-65 ký tự cho SEO) |
| `content` | ✅ | Nội dung HTML |
| `category` | | Slug hoặc ID (auto-create nếu chưa tồn tại) |
| `excerpt` | | Mô tả ngắn (80-200 ký tự) |
| `is_featured` | | Default: `false` |
| `is_published` | | Default: `true` |
| `cover_image_url` | | URL ảnh → auto download + WebP + responsive |
| `auto_placeholder` | | Default: `true` — tạo placeholder nếu không có ảnh |
| `skip_seo_validation` | | Default: `false` |
| `meta_title` | | SEO title (50-60 ký tự) |
| `meta_description` | | SEO description (120-155 ký tự) |
| `meta_keywords` | | Comma-separated keywords |
| `source_url` | | URL nguồn gốc |
| `source_id` | | ID nguồn (dùng tìm lại khi update) |
| `workflow_id` | | N8N workflow ID |
| `execution_id` | | N8N execution ID |
| `is_ai_generated` | | Boolean |
| `ai_model` | | Model name (gpt-4, gemini...) |

**SEO Content Requirements (nếu không skip):**
- `content`: ≥600 từ, KHÔNG `<h1>`, tối thiểu 3 `<h2>` (có id), bắt đầu bằng `<p>`, KHÔNG inline styles
- `excerpt`: 80-200 ký tự

**Image Pipeline:**
1. Download URL → convert WebP → responsive sizes (480w, 768w, 1200w, 1920w)
2. Auto thumbnail (400×267px) + og_image cho social sharing
3. Không có ảnh → auto placeholder từ title

**Response (201):**
```json
{
  "success": true,
  "article": {
    "id": 1,
    "title": "...",
    "slug": "tieu-de-bai-viet",
    "url": "/tin-tuc/tieu-de-bai-viet",
    "is_published": true,
    "created_at": "2026-02-25T12:00:00Z",
    "cover_image": "/media/news/covers/unstressvn-tieu-de-bai-viet-cover.webp",
    "thumbnail": "/media/news/thumbnails/...",
    "has_responsive_images": true
  },
  "image_source": "url",
  "seo_warnings": [],
  "message": "Đã tạo bài viết tin tức thành công"
}
```

### 3.2 Danh sách tin tức

```http
GET /api/v1/n8n/news/list/
```

**Query params:**

| Param | Mô tả |
|-------|-------|
| `page` | Default: 1 |
| `page_size` | Default: 20, max: 100 |
| `category` | Slug category |
| `is_published` | `true` / `false` |
| `search` | Tìm trong title |
| `source` | Filter theo source (n8n, admin...) |

**Response:**
```json
{
  "success": true,
  "total": 45,
  "page": 1,
  "page_size": 20,
  "results": [
    {
      "id": 1, "title": "...", "slug": "...", "url": "/tin-tuc/...",
      "is_published": true, "is_featured": false, "view_count": 123,
      "created_at": "...", "updated_at": "...",
      "category": "hoc-tieng-duc",
      "cover_image": "/media/...",
      "source": "n8n", "source_id": "..."
    }
  ]
}
```

### 3.3 Cập nhật tin tức

```http
PUT/PATCH /api/v1/n8n/news/<identifier>/
```

`identifier` = slug, id, hoặc source_id. Body chứa bất kỳ field nào cần cập nhật.
Thêm `"regenerate_slug": true` để tạo lại slug khi đổi title.
Khi `is_published` chuyển false→true sẽ tự động set `published_at`.

**Response:**
```json
{
  "success": true,
  "article": { "id": 1, "title": "...", "slug": "...", "url": "...", "updated_at": "..." },
  "updated_fields": ["title", "content", "is_featured"],
  "image_source": "unchanged",
  "message": "Đã cập nhật bài viết news thành công"
}
```

---

## 4. Knowledge — Kiến thức

### 4.1 Tạo bài viết

```http
POST /api/v1/n8n/knowledge/
Content-Type: application/json
```

Giống News, thêm:

| Field | Mô tả | Default |
|-------|-------|---------|
| `language` | `de`, `en`, `all` | `all` |
| `level` | `A1`, `A2`, `B1`, `B2`, `C1`, `C2`, `all` | `all` |

### 4.2 Danh sách

```http
GET /api/v1/n8n/knowledge/list/?language=de&level=B1&page=1
```

Thêm filter: `language`, `level` (ngoài params chung).

### 4.3 Cập nhật

```http
PUT/PATCH /api/v1/n8n/knowledge/<identifier>/
```

Giống News update, thêm `language` + `level`.

---

## 5. Tools — Công cụ học tập

### 5.1 Tạo công cụ

```http
POST /api/v1/n8n/tools/
Content-Type: application/json
```

| Field | Bắt buộc | Mô tả |
|-------|----------|-------|
| `name` | ✅ | Tên công cụ |
| `description` | ✅ | Mô tả |
| `tool_type` | | `article` (default), `internal`, `external`, `embed` |
| `content` | | Nội dung HTML (cho article type) |
| `category` | | Slug hoặc ID (auto-create) |
| `url` | | URL (bắt buộc cho external type) |
| `embed_code` | | iframe HTML (cho embed type) |
| `icon` | | lucide-react icon name |
| `language` | | `en`, `de`, `all` (default: `all`) |
| `excerpt` | | Mô tả ngắn |
| `is_featured` | | Default: `false` |
| `is_published` | | Default: `true` |
| `cover_image_url` | | URL ảnh bìa |
| `auto_placeholder` | | Default: `true` |
| `meta_title` | | SEO title |
| `meta_description` | | SEO description |
| `skip_seo_validation` | | Default: `false` (áp dụng cho article type) |

**Response (201):**
```json
{
  "success": true,
  "tool": {
    "id": 3,
    "name": "Từ điển Deutsch-Vietnamesisch",
    "slug": "tu-dien-deutsch-vietnamesisch",
    "tool_type": "external",
    "language": "de",
    "url": "/cong-cu/tu-dien-deutsch-vietnamesisch",
    "is_published": true,
    "cover_image": null,
    "created_at": "2026-02-25T12:00:00Z"
  },
  "image_source": "none",
  "message": "Đã tạo công cụ thành công"
}
```

### 5.2 Danh sách

```http
GET /api/v1/n8n/tools/list/?tool_type=article&language=de&is_published=true
```

| Filter | Mô tả |
|--------|-------|
| `tool_type` | `internal`, `external`, `embed`, `article` |
| `language` | `en`, `de`, `all` |
| `is_published` | `true` / `false` |
| `category` | Slug |
| `search` | Tìm trong name |

### 5.3 Cập nhật

```http
PUT/PATCH /api/v1/n8n/tools/<identifier>/
```

`identifier` = slug hoặc id. Body chứa bất kỳ field nào cần update.
Hỗ trợ `regenerate_slug`, `cover_image_url`, tất cả text + boolean fields.

---

## 6. Resources — Tài liệu

### 6.1 Tạo tài liệu

```http
POST /api/v1/n8n/resources/
Content-Type: application/json
```

| Field | Bắt buộc | Mô tả |
|-------|----------|-------|
| `title` | ✅ | Tên tài liệu |
| `description` | ✅ | Mô tả |
| `category` | | Slug hoặc ID |
| `resource_type` | | `ebook`, `book`, `pdf`, `audio`, `video`, `document`, `flashcard` |
| `external_url` | | URL file |
| `youtube_url` | | YouTube URL |
| `author` | | Tác giả (text) |
| `is_featured` | | Default: `false` |
| `source_url`, `source_id`, `workflow_id`... | | N8N tracking |

### 6.2 Danh sách

```http
GET /api/v1/n8n/resources/list/?resource_type=ebook&category=sach
```

Filter: `resource_type`, `category`, `search`, `source`.

### 6.3 Cập nhật

```http
PUT/PATCH /api/v1/n8n/resources/<identifier>/
```

`identifier` = slug, id, hoặc source_id. Hỗ trợ tất cả fields, `regenerate_slug`, `cover_image_url`, N8N tracking.

---

## 7. Videos — YouTube

### 7.1 Tạo video

```http
POST /api/v1/n8n/videos/
Content-Type: application/json
```

| Field | Bắt buộc | Mô tả |
|-------|----------|-------|
| `youtube_id` | ✅ | YouTube video ID hoặc full URL |
| `title` | | Auto-fetch từ YouTube nếu bỏ qua |
| `description` | | |
| `language` | | `en` (default), `de`, `all` |
| `level` | | `A1`-`C2`, `all` (default) |
| `is_featured` | | Default: `false` |
| `source_url`, `source_id`... | | N8N tracking |

Auto duplicate check theo `youtube_id` và `source_id`. Nếu trùng, trả 200 + `action: "skipped"`.

### 7.2 Danh sách

```http
GET /api/v1/n8n/videos/list/?language=de&level=B1&search=keyword
```

Filter: `language`, `level`, `search`, `source`.

---

## 8. Flashcards — Bộ thẻ từ vựng

### 8.1 Tạo bộ flashcard (deck + cards)

```http
POST /api/v1/n8n/flashcards/
Content-Type: application/json
```

```json
{
  "name": "500 từ vựng B1 tiếng Đức",
  "description": "Bộ từ vựng cơ bản cho trình độ B1",
  "language": "de",
  "level": "B1",
  "is_public": true,
  "is_featured": false,
  "cards": [
    {
      "front": "der Hund",
      "back": "con chó",
      "example": "Der Hund ist groß.",
      "pronunciation": "/hʊnt/",
      "audio_url": "https://..."
    },
    {
      "front": "die Katze",
      "back": "con mèo",
      "example": "Die Katze schläft."
    }
  ]
}
```

| Field | Bắt buộc | Mô tả |
|-------|----------|-------|
| `name` | ✅ | Tên bộ flashcard |
| `language` | ✅ | `en` hoặc `de` |
| `level` | ✅ | `A1`-`C2` |
| `description` | | Mô tả |
| `is_public` | | Default: `true` |
| `is_featured` | | Default: `false` |
| `cards` | | Mảng các thẻ (mỗi thẻ cần `front` + `back`) |

Auto duplicate check theo `name + language + level`.

**Card fields:**

| Field | Bắt buộc | Mô tả |
|-------|----------|-------|
| `front` | ✅ | Mặt trước (từ vựng) |
| `back` | ✅ | Mặt sau (nghĩa) |
| `example` | | Câu ví dụ |
| `pronunciation` | | Phiên âm |
| `audio_url` | | URL file audio |

**Response (201):**
```json
{
  "success": true,
  "deck": {
    "id": 5,
    "name": "500 từ vựng B1 tiếng Đức",
    "slug": "500-tu-vung-b1-tieng-duc",
    "language": "de",
    "level": "B1",
    "url": "/cong-cu/flashcards/500-tu-vung-b1-tieng-duc",
    "created_at": "2026-02-25T12:00:00Z"
  },
  "cards_created": 2,
  "message": "Đã tạo bộ flashcard với 2 thẻ",
  "action": "created"
}
```

### 8.2 Cập nhật bộ flashcard

```http
PUT/PATCH /api/v1/n8n/flashcards/<identifier>/
```

`identifier` = slug hoặc id.

| Field | Mô tả |
|-------|-------|
| `name` | Đổi tên |
| `description` | Đổi mô tả |
| `language` | `en` / `de` |
| `level` | `A1`-`C2` |
| `is_public` | Boolean |
| `is_featured` | Boolean |
| `add_cards` | Mảng thẻ mới — thêm vào cuối |
| `replace_cards` | Mảng thẻ mới — XOÁ HẾT thẻ cũ, thay bằng mới |

**Lưu ý:** `add_cards` và `replace_cards` không dùng đồng thời. Nếu cả 2 được gửi, `replace_cards` có ưu tiên.

---

## 9. Stream Media — Video GDrive

### 9.1 Tạo video streaming

```http
POST /api/v1/n8n/stream-media/
Content-Type: application/json
```

```json
{
  "title": "Phim Đức - Tschick",
  "description": "Phim Đức hay cho trình độ B1",
  "media_type": "video",
  "storage_type": "gdrive",
  "gdrive_url": "https://drive.google.com/file/d/1ABC.../view",
  "category": "phim-duc",
  "language": "de",
  "level": "B1",
  "tags": "phim, đức, B1",
  "transcript": "Nội dung transcript...",
  "is_public": true,
  "requires_login": false
}
```

| Field | Bắt buộc | Mô tả |
|-------|----------|-------|
| `title` | ✅ | Tiêu đề video |
| `gdrive_url` | ✅ (gdrive) | Google Drive URL (auto trích xuất file ID) |
| `description` | | Mô tả |
| `media_type` | | `video` (default) hoặc `audio` |
| `storage_type` | | `gdrive` (default) hoặc `local` |
| `category` | | Slug hoặc ID (auto-create) |
| `language` | | `vi`, `en`, `de`, `all` (default: `all`) |
| `level` | | `A1`-`C2`, `all` (default: `all`) |
| `tags` | | Comma-separated tags |
| `transcript` | | Transcript nội dung |
| `is_public` | | Default: `true` |
| `requires_login` | | Default: `false` |

Auto duplicate check theo `gdrive_url`.

**Response (201):**
```json
{
  "success": true,
  "media": {
    "id": 3,
    "uid": "a1b2c3d4-...",
    "title": "Phim Đức - Tschick",
    "slug": "phim-duc-tschick",
    "storage_type": "gdrive",
    "gdrive_file_id": "1ABC...",
    "media_type": "video",
    "stream_url": "/media-stream/play/a1b2c3d4-.../",
    "language": "de",
    "level": "B1",
    "created_at": "2026-02-25T12:00:00Z"
  },
  "message": "Đã tạo stream media thành công",
  "action": "created"
}
```

---

## 10. Delete — Xoá nội dung

```http
DELETE /api/v1/n8n/<content_type>/<identifier>/delete/
```

| Param | Mô tả |
|-------|-------|
| `content_type` | `news`, `knowledge`, `resources`, `tools`, `videos`, `stream-media`, `flashcards` |
| `identifier` | slug, id, uid (stream-media), hoặc source_id |

**Query params:**
- `?hard=true` — Xoá vĩnh viễn (KHÔNG THỂ HOÀN TÁC)

**Soft delete (mặc định):**
- News/Knowledge: `is_published = False`
- Resources/Tools/Videos/StreamMedia: `is_active = False`
- Flashcards: `is_public = False`

**Response:**
```json
{
  "success": true,
  "action": "soft_delete",
  "field_changed": "is_published",
  "message": "Đã ẩn \"Tiêu đề bài viết\" (soft delete: is_published=False)"
}
```

Hard delete:
```json
{
  "success": true,
  "action": "hard_delete",
  "message": "Đã xoá vĩnh viễn \"Tiêu đề bài viết\""
}
```

---

## 11. Bulk — Tạo hàng loạt

```http
POST /api/v1/n8n/bulk/
Content-Type: application/json
```

```json
{
  "content_type": "news",
  "skip_seo_validation": true,
  "items": [
    {"title": "Bài 1", "content": "<p>...</p>", "category": "hoc-tieng-duc"},
    {"title": "Bài 2", "content": "<p>...</p>", "category": "doi-song"},
    {"title": "Bài 3", "content": "<p>...</p>"}
  ]
}
```

| Field | Bắt buộc | Mô tả |
|-------|----------|-------|
| `content_type` | ✅ | `news`, `knowledge`, `tools`, `resources`, `videos`, `flashcards`, `stream-media` |
| `items` | ✅ | Mảng items (max 50), mỗi item cùng format endpoint CREATE tương ứng |
| `skip_seo_validation` | | Default: `true` cho bulk |

**Auto dedup:** Skip duplicate theo slug (hoặc youtube_id, gdrive_url, name+language+level).

**Response:**
```json
{
  "success": true,
  "content_type": "news",
  "total": 3,
  "created": 2,
  "skipped": 1,
  "failed": 0,
  "results": [
    {"index": 0, "status": "created", "id": 15, "title": "Bài 1", "slug": "bai-1"},
    {"index": 1, "status": "skipped", "reason": "duplicate", "id": 8, "title": "Bài 2"},
    {"index": 2, "status": "created", "id": 16, "title": "Bài 3", "slug": "bai-3"}
  ]
}
```

---

## N8N Tracking Fields

Các model hỗ trợ tracking (News, Knowledge, Resources, Videos):

| Field | Mô tả |
|-------|--------|
| `source_url` | URL nguồn gốc nội dung |
| `source_id` | ID từ nguồn — dùng để tìm lại khi update |
| `workflow_id` | N8N workflow ID |
| `execution_id` | N8N execution ID |
| `is_ai_generated` | Boolean — nội dung do AI tạo |
| `ai_model` | Model AI đã dùng (gpt-4, gemini...) |

**Lưu ý:** Tools, Flashcards, Stream Media KHÔNG có N8N tracking fields.

---

## Error Handling

### Field Auto-Truncation

API tự động cắt ngắn CharField vượt giới hạn DB (thay vì crash 500):

| Field | Max Length | Áp dụng cho |
|-------|-----------|-------------|
| `title` / `name` | 200-255 | Tất cả models |
| `meta_title` | 70 | News, Knowledge |
| `meta_description` | 160 | News, Knowledge |
| `meta_keywords` | 255 | News, Knowledge |
| `excerpt` | 500 | News, Knowledge |
| `source_url` | 200 | N8N tracking |
| `ai_model` | 50 | N8N tracking |

### Status codes

| Code | Ý nghĩa |
|------|---------|
| 200 | Thành công (update, list, skip duplicate) |
| 201 | Tạo mới thành công |
| 400 | Thiếu field bắt buộc / SEO validation fail / invalid data |
| 403 | API Key không hợp lệ hoặc hết hạn |
| 404 | Không tìm thấy object |
| 500 | Server error (trả JSON chi tiết, không HTML) |

> **Tất cả error responses đều trả JSON** — không bao giờ trả HTML.

### Error Response Format

**Lỗi validation (400):**
```json
{
  "success": false,
  "error": "Mô tả lỗi bằng tiếng Việt",
  "seo_errors": ["..."],
  "seo_warnings": ["..."],
  "hint": "Gửi skip_seo_validation=true để bỏ qua"
}
```

**Lỗi xác thực (403):**
```json
{
  "success": false,
  "error": "API Key không hợp lệ hoặc đã hết hạn",
  "status_code": 403
}
```

**Lỗi server (500):**
```json
{
  "success": false,
  "error": "TypeError: Chi tiết lỗi...",
  "hint": "Lỗi hệ thống không mong muốn. Kiểm tra dữ liệu gửi và thử lại.",
  "path": "/api/v1/n8n/news/"
}
```

### SEO Validation Errors (HTTP 400)

```json
{
  "success": false,
  "error": "Nội dung không đạt chuẩn SEO",
  "seo_errors": [
    "Nội dung cần ít nhất 600 từ (hiện có 150 từ)",
    "Nội dung KHÔNG được chứa thẻ <h1>",
    "Cần ít nhất 3 thẻ <h2> có id"
  ],
  "seo_warnings": ["Title nên dài 40-65 ký tự"],
  "hint": "Gửi skip_seo_validation=true để bỏ qua"
}
```

---

## Image Pipeline

Áp dụng cho News, Knowledge, Tools, Resources.

**3 phương thức (theo thứ tự ưu tiên):**
1. `cover_image` (file upload): multipart/form-data
2. `cover_image_url` (URL): Auto download + convert
3. `auto_placeholder` (boolean): Tạo placeholder từ title

**Pipeline xử lý:**
1. Download/upload → convert WebP (chất lượng cao)
2. Tạo thumbnail 400×267px
3. Tạo responsive sizes: 480w, 768w, 1200w, 1920w (cho srcset)
4. Copy sang og_image cho social media
5. Nếu không có ảnh + `auto_placeholder=true` → tạo placeholder gradient

---

## Ví dụ N8N Workflow

### 1. Thu thập tin tức → Đăng bài tự động

```
RSS Feed → Extract Content → AI Rewrite → HTTP Request (POST /news/)
```

```json
{
  "method": "POST",
  "url": "https://unstressvn.com/api/v1/n8n/news/",
  "headers": {"X-API-Key": "{{$env.API_KEY}}"},
  "body": {
    "title": "{{$json.title}}",
    "content": "{{$json.ai_content}}",
    "source_url": "{{$json.link}}",
    "source_id": "{{$json.guid}}",
    "workflow_id": "{{$workflow.id}}",
    "execution_id": "{{$execution.id}}",
    "is_ai_generated": true,
    "ai_model": "gpt-4"
  }
}
```

### 2. Tạo flashcard từ AI

```
Topic Input → Gemini Generate → Parse JSON → HTTP Request (POST /flashcards/)
```

```json
{
  "method": "POST",
  "url": "https://unstressvn.com/api/v1/n8n/flashcards/",
  "headers": {"X-API-Key": "{{$env.API_KEY}}"},
  "body": {
    "name": "Từ vựng chủ đề {{$json.topic}}",
    "language": "de",
    "level": "B1",
    "cards": "{{$json.generated_cards}}"
  }
}
```

### 3. Bulk import từ CSV

```
Read CSV → Split Batches (50) → HTTP Request (POST /bulk/)
```

```json
{
  "method": "POST",
  "url": "https://unstressvn.com/api/v1/n8n/bulk/",
  "headers": {"X-API-Key": "{{$env.API_KEY}}"},
  "body": {
    "content_type": "knowledge",
    "skip_seo_validation": true,
    "items": "{{$json.batch}}"
  }
}
```

### 4. Google Drive → Stream Media

```
Google Drive Trigger → Get File Info → HTTP Request (POST /stream-media/)
```

```json
{
  "method": "POST",
  "url": "https://unstressvn.com/api/v1/n8n/stream-media/",
  "headers": {"X-API-Key": "{{$env.API_KEY}}"},
  "body": {
    "title": "{{$json.name}}",
    "gdrive_url": "{{$json.webViewLink}}",
    "category": "phim-duc",
    "language": "de"
  }
}
```

### 5. Kiểm tra + Update nội dung

```
Schedule Trigger → List News → Check Quality → Update Bad Articles
```

```json
// Step 1: List
{"method": "GET", "url": "https://unstressvn.com/api/v1/n8n/news/list/?source=n8n&is_published=true"}

// Step 2: Update
{"method": "PATCH", "url": "https://unstressvn.com/api/v1/n8n/news/{{$json.slug}}/",
 "body": {"content": "{{$json.improved_content}}", "skip_seo_validation": true}}
```

---

## API Key Management

API Keys quản lý qua Django Admin:
- URL: `https://unstressvn.com/admin/core/apikey/`
- Tạo key với name: `n8n_api_key`
- Có thể deactivate khi cần

---

## Rate Limits

Hiện tại không có rate limit. Khuyến nghị:
- Tối đa 100 requests/phút
- Delay 1-2 giây giữa requests
- Dùng `/bulk/` cho batch operations thay vì gọi từng endpoint

---

## Contact

Email: unstressvn@gmail.com
