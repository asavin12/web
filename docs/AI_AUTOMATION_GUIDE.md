# 🤖 HƯỚNG DẪN TỰ ĐỘNG HÓA NỘI DUNG — UNSTRESSVN

> **Tài liệu này dành cho AI đọc.** Chứa toàn bộ thông tin cần thiết để AI (GPT-4, Claude, Gemini...)
> có thể tạo script automation đăng bài đúng form, đúng mục cho website UnstressVN.
>
> **Cập nhật:** 2026-02-28 (v2 — đồng bộ navigation, tags, categories thực tế)

---

## MỤC LỤC

1. [Tổng quan hệ thống](#1-tổng-quan-hệ-thống)
2. [Xác thực API](#2-xác-thực-api)
3. [Database Schema — Tất cả Models](#3-database-schema)
4. [Chuẩn SEO bắt buộc](#4-chuẩn-seo-bắt-buộc)
5. [Template HTML mẫu cho content](#5-template-html-mẫu)
6. [Tất cả API Endpoints](#6-api-endpoints)
7. [Hệ thống Categories](#7-hệ-thống-categories)
8. [Scripts mẫu Python — Automation](#8-scripts-mẫu-python)
9. [Prompts AI tạo nội dung](#9-prompts-ai)
10. [N8N Workflows mẫu](#10-n8n-workflows)
11. [Xử lý lỗi](#11-xử-lý-lỗi)
12. [Hệ thống xoá dữ liệu mẫu](#12-xoá-dữ-liệu-mẫu)

---

## 1. TỔNG QUAN HỆ THỐNG

### Website

| Thông tin | Giá trị |
|-----------|---------|
| Tên | **UnstressVN** — Nền tảng học ngoại ngữ miễn phí |
| URL | `https://unstressvn.com` |
| Đối tượng | Người Việt học tiếng Đức và tiếng Anh |
| Kiến trúc | Headless CMS — Django API + React SPA |
| API Base | `https://unstressvn.com/api/v1/n8n/` |
| Backend | Django 4.2 + DRF + PostgreSQL |
| Frontend | React 19 + TypeScript + Tailwind CSS 4 |

### 7 loại nội dung

| # | Loại | URL Frontend | API Endpoint | Mô tả |
|---|------|-------------|--------------|-------|
| 1 | **News** | `/tin-tuc/{slug}` | `/n8n/news/` | Tin tức du học, học bổng, đời sống |
| 2 | **Knowledge** | `/kien-thuc/{slug}` | `/n8n/knowledge/` | Bài giảng ngữ pháp, từ vựng, kỹ năng |
| 3 | **Tools** | `/cong-cu/{slug}` | `/n8n/tools/` | Công cụ học tập (từ điển, bài viết...) |
| 4 | **Resources** | `/tai-lieu/{slug}` | `/n8n/resources/` | Ebook, PDF, tài liệu tham khảo |
| 5 | **Videos** | `/video/{slug}` | `/n8n/videos/` | Video YouTube hướng dẫn |
| 6 | **Flashcards** | `/cong-cu/flashcards/{slug}` | `/n8n/flashcards/` | Bộ thẻ từ vựng |
| 7 | **Stream Media** | `/stream/{uid}` | `/n8n/stream-media/` | Video streaming từ Google Drive |

### Ngôn ngữ & Trình độ (CEFR)

**Languages:** `en` (English), `de` (German), `all` (Tất cả). StreamMedia thêm `vi` (Vietnamese).

**Levels:** `A1` (Sơ cấp), `A2` (Sơ trung), `B1` (Trung cấp), `B2` (Trung cao), `C1` (Cao cấp), `C2` (Thành thạo), `all` (Tất cả).

---

## 2. XÁC THỰC API

### Header bắt buộc

```
X-API-Key: <API_KEY>
Content-Type: application/json
```

### Cách lấy API Key

1. Đăng nhập Admin: `https://unstressvn.com/admin/core/apikey/`
2. Tạo key mới với name: `n8n_api_key`
3. Copy key value → dùng trong header `X-API-Key`

### Health check (không cần auth)

```bash
curl https://unstressvn.com/api/v1/n8n/health/
```

### Ví dụ gọi API bằng Python

```python
import requests

API_URL = "https://unstressvn.com/api/v1/n8n"
API_KEY = "your-api-key-here"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Health check
r = requests.get(f"{API_URL}/health/")
print(r.json())  # {"status": "ok", "service": "UnstressVN API", ...}
```

---

## 3. DATABASE SCHEMA

### 3.1 News Article (`news.Article`)

| Field | Type | Bắt buộc | Mô tả |
|-------|------|----------|-------|
| `title` | CharField(255) | ✅ | Tiêu đề (40-65 ký tự cho SEO). **Auto-truncate** nếu > 255 |
| `slug` | SlugField(280) | Auto | Tự tạo từ title (tiếng Việt không dấu) |
| `content` | TextField | ✅ | Nội dung HTML chuẩn SEO |
| `excerpt` | TextField(500) | | Mô tả ngắn (80-200 ký tự) |
| `category` | FK → news.Category | | Slug hoặc ID |
| `author` | FK → User | Auto | Bot user `automation_bot` |
| `cover_image` | ImageField | Auto | WebP, auto-pipeline |
| `thumbnail` | ImageField | Auto | 400×267px |
| `is_published` | BooleanField | | Default: True |
| `is_featured` | BooleanField | | Default: False |
| `published_at` | DateTimeField | Auto | Auto set khi publish |
| `view_count` | IntegerField | Auto | Mặc định 0 |
| `meta_title` | CharField(70) | | SEO title (50-60 ký tự). **Auto-truncate** nếu > 70 |
| `meta_description` | CharField(160) | | SEO description (120-155 ký tự). **Auto-truncate** nếu > 160 |
| `meta_keywords` | CharField(255) | | 3-7 keywords, comma-separated. **Auto-truncate** nếu > 255 |
| `tags` | CharField(255) | | Tags SEO, comma-separated (VD: "học bổng, DAAD, du học Đức"). **Auto-generate** nếu để trống |
| `og_image` | ImageField | Auto | Copy từ cover_image |
| **N8N Tracking:** | | | |
| `source` | CharField(20) | Auto | `n8n` (auto set) |
| `source_url` | URLField | | URL nguồn gốc nội dung |
| `source_id` | CharField(100) | | ID từ nguồn (tìm lại khi update) |
| `n8n_workflow_id` | CharField(50) | | Workflow ID |
| `n8n_execution_id` | CharField(100) | | Execution ID |
| `is_ai_generated` | BooleanField | | Nội dung do AI tạo |
| `ai_model` | CharField(50) | | Model name (gpt-4, gemini...) |

### 3.2 Knowledge Article (`knowledge.KnowledgeArticle`)

Giống News Article (bao gồm `tags`), **thêm:**

| Field | Type | Mô tả |
|-------|------|-------|
| `language` | CharField(5) | `en`, `de`, `all` (default: `all`) |
| `level` | CharField(5) | `A1`-`C2`, `all` (default: `all`) |
| `schema_type` | CharField(20) | `Article`, `HowTo`, `FAQPage`, `Course` |

### 3.3 Tool (`tools.Tool`)

| Field | Type | Bắt buộc | Mô tả |
|-------|------|----------|-------|
| `name` | CharField(200) | ✅ | Tên công cụ |
| `slug` | SlugField(220) | Auto | Tự tạo |
| `description` | TextField | ✅ | Mô tả |
| `content` | TextField | | HTML cho article type |
| `excerpt` | TextField | | Mô tả ngắn |
| `category` | FK → ToolCategory | | Slug hoặc ID |
| `tool_type` | CharField(20) | | `article` (mặc định), `internal`, `external`, `embed` |
| `url` | CharField(500) | | URL (bắt buộc cho external) |
| `embed_code` | TextField | | iframe (cho embed) |
| `icon` | CharField(50) | | lucide-react icon name |
| `language` | CharField(5) | | `en`, `de`, `all` |
| `cover_image` | ImageField | Auto | WebP pipeline |
| `is_published` | BooleanField | | Default: True |
| `is_featured` | BooleanField | | Default: False |
| `is_active` | BooleanField | | Default: True |
| `meta_title` | CharField(200) | | SEO title |
| `meta_description` | TextField | | SEO description |

> **⚠️ Tool KHÔNG có N8N tracking fields** (source, source_id...).

### 3.4 Resource (`resources.Resource`)

| Field | Type | Bắt buộc | Mô tả |
|-------|------|----------|-------|
| `title` | CharField(200) | ✅ | Tên tài liệu |
| `slug` | SlugField(200) | Auto | |
| `description` | TextField | ✅ | Mô tả |
| `category` | FK → resources.Category | | |
| `resource_type` | CharField(20) | | `book`, `ebook`, `audio`, `document`, `pdf`, `flashcard`, `video` |
| `file` | FileField | | Upload file trực tiếp |
| `youtube_url` | URLField | | YouTube URL |
| `external_url` | URLField | | Link tải bên ngoài |
| `cover_image` | ImageField | | Ảnh bìa |
| `author` | CharField(100) | | Tên tác giả (text, KHÔNG phải FK) |
| `is_active` | BooleanField | | Default: True |
| `is_featured` | BooleanField | | Default: False |
| **+ N8N Tracking fields** | | | source, source_id, workflow_id... |

### 3.5 Video (`core.Video`)

| Field | Type | Bắt buộc | Mô tả |
|-------|------|----------|-------|
| `title` | CharField(255) | Auto | Auto-fetch từ YouTube |
| `slug` | SlugField(300) | Auto | |
| `youtube_id` | CharField(100) | ✅ | ID hoặc full URL |
| `description` | TextField | | |
| `thumbnail` | URLField | Auto | Auto-fetch |
| `language` | CharField(5) | | `en` (default), `de`, `all` |
| `level` | CharField(5) | | `A1`-`C2`, `all` |
| `is_featured` | BooleanField | | Default: False |
| `is_active` | BooleanField | | Default: True |
| **+ N8N Tracking fields** | | | |

### 3.6 FlashcardDeck (`tools.FlashcardDeck`)

| Field | Type | Bắt buộc | Mô tả |
|-------|------|----------|-------|
| `name` | CharField(200) | ✅ | Tên bộ flashcard |
| `slug` | SlugField(220) | Auto | |
| `description` | TextField | | Mô tả |
| `language` | CharField(5) | ✅ | `en` hoặc `de` |
| `level` | CharField(5) | ✅ | `A1`-`C2` |
| `is_public` | BooleanField | | Default: True |
| `is_featured` | BooleanField | | Default: False |

**Flashcard (thẻ con):**

| Field | Type | Bắt buộc | Mô tả |
|-------|------|----------|-------|
| `front` | TextField | ✅ | Mặt trước (từ vựng / câu hỏi) |
| `back` | TextField | ✅ | Mặt sau (nghĩa / đáp án) |
| `example` | TextField | | Câu ví dụ |
| `pronunciation` | CharField(200) | | Phiên âm IPA |
| `audio_url` | URLField | | URL file audio phát âm |
| `order` | IntegerField | Auto | Thứ tự |

> **⚠️ Flashcard KHÔNG có N8N tracking fields.**

### 3.7 StreamMedia (`mediastream.StreamMedia`)

| Field | Type | Bắt buộc | Mô tả |
|-------|------|----------|-------|
| `title` | CharField(255) | ✅ | Tiêu đề |
| `slug` | SlugField(255) | Auto | |
| `uid` | UUID | Auto | Unique ID cho URL stream |
| `storage_type` | CharField(10) | | `local`, `gdrive` (default: `gdrive`) |
| `media_type` | CharField(10) | | `video`, `audio` |
| `gdrive_url` | URLField(500) | ✅ (gdrive) | Google Drive URL |
| `gdrive_file_id` | CharField(255) | Auto | Tự trích xuất từ URL |
| `description` | TextField | | |
| `transcript` | TextField | | Transcript nội dung |
| `category` | FK → MediaCategory | | |
| `language` | CharField(10) | | `vi`, `en`, `de`, `all` |
| `level` | CharField(10) | | `A1`-`C2`, `all` |
| `tags` | CharField(500) | | Comma-separated |
| `is_public` | BooleanField | | Default: True |
| `is_active` | BooleanField | | Default: True |
| `requires_login` | BooleanField | | Default: False |

> **⚠️ StreamMedia KHÔNG có N8N tracking fields.**

---

## 4. CHUẨN SEO BẮT BUỘC

### 4.1 Tiêu đề (`title`)

| Quy tắc | Chi tiết |
|---------|---------|
| Độ dài | **40-65 ký tự** (tối ưu 55-60) |
| Từ khóa | Đặt từ khóa chính **ở đầu** tiêu đề |
| Số liệu | Ưu tiên con số ("Top 10...", "5 cách...") |
| Năm | Thêm năm nếu cập nhật ("2026") |
| Format | `[Từ khóa chính]: [Lợi ích/Chi tiết]` |

### 4.2 Nội dung (`content`) — Quy tắc validation

API sẽ **tự động kiểm tra** (gửi `skip_seo_validation: true` để bỏ qua):

| Quy tắc | Lỗi/Cảnh báo |
|---------|--------------|
| `≥ 600 từ` | **LỖI** nếu < 100 từ, cảnh báo nếu < 600 |
| Không `<h1>` | **LỖI** — title đã là H1 |
| `≥ 3 thẻ <h2>` | **LỖI** nếu 0, cảnh báo nếu < 3 |
| `<h2>` có `id=""` | Cảnh báo nếu thiếu (cho anchor link) |
| Bắt đầu bằng `<p>` | Cảnh báo |
| Không inline styles | **LỖI** nếu có `style="..."` |
| Không thẻ lỗi thời | **LỖI** nếu có `<font>`, `<center>`, `<marquee>` |
| Có danh sách | Cảnh báo nếu không có `<ul>` hoặc `<ol>` |
| Có kết luận | Cảnh báo nếu không có `<h2>...Kết luận...</h2>` |

### 4.3 Meta fields

| Field | Độ dài | Format |
|-------|--------|--------|
| `meta_title` | 50-60 ký tự | `[Từ khóa chính] — [Bổ sung] \| UnstressVN` |
| `meta_description` | 120-155 ký tự | Chứa từ khóa + lời kêu gọi hành động |
| `excerpt` | 80-200 ký tự | Tóm tắt giá trị bài viết |
| `meta_keywords` | 3-7 keywords | Comma-separated, từ khóa chính đầu tiên |

### 4.4 Các thẻ HTML ĐƯỢC PHÉP

```
✅ <p>, <h2 id="">, <h3>, <h4>
✅ <ul>, <ol>, <li>
✅ <strong>, <em>
✅ <a href="">, <blockquote>
✅ <table>, <thead>, <tbody>, <tr>, <th>, <td>
✅ <figure>, <figcaption>, <img alt="" loading="lazy">
✅ <iframe> (YouTube), <nav>, <hr>
✅ <code>, <pre>
```

### 4.5 CẤM sử dụng

```
❌ <h1> — title đã là H1
❌ <div style="">, <span style="">
❌ <br> thay cho <p>
❌ <font>, <center>, <b>, <i>, <marquee>
❌ Inline CSS: style="..."
❌ JavaScript
```

---

## 5. TEMPLATE HTML MẪU

### 5.1 Template chuẩn cho `content` (bài News / Knowledge / Tool article)

```html
<p>[Từ khóa chính] là... [Mô tả ngắn]. Trong bài viết này, bạn sẽ tìm hiểu [lợi ích 1], [lợi ích 2] và [lợi ích 3].</p>

<nav>
  <h2>Nội dung bài viết</h2>
  <ul>
    <li><a href="#phan-1">1. [Tiêu đề phần 1]</a></li>
    <li><a href="#phan-2">2. [Tiêu đề phần 2]</a></li>
    <li><a href="#phan-3">3. [Tiêu đề phần 3]</a></li>
    <li><a href="#ket-luan">Kết luận</a></li>
  </ul>
</nav>

<hr>

<h2 id="phan-1">1. [Tiêu đề — chứa từ khóa phụ]</h2>

<p>[Nội dung 3-5 câu. Topic sentence ở đầu.]</p>

<p>[Đoạn bổ sung thêm.]</p>

<blockquote>
  <p><strong>💡 Mẹo:</strong> [Thông tin hữu ích cho người học.]</p>
</blockquote>

<h2 id="phan-2">2. [Tiêu đề — chứa từ khóa phụ]</h2>

<p>[Nội dung phần 2...]</p>

<ul>
  <li><strong>[Điểm 1]:</strong> [Giải thích]</li>
  <li><strong>[Điểm 2]:</strong> [Giải thích]</li>
  <li><strong>[Điểm 3]:</strong> [Giải thích]</li>
</ul>

<h2 id="phan-3">3. [Tiêu đề]</h2>

<p>[Nội dung phần 3...]</p>

<h3>3.1. [Mục con]</h3>

<p>[Chi tiết...]</p>

<ol>
  <li><strong>Bước 1:</strong> [Hành động cụ thể]</li>
  <li><strong>Bước 2:</strong> [Hành động cụ thể]</li>
  <li><strong>Bước 3:</strong> [Hành động cụ thể]</li>
</ol>

<table>
  <thead>
    <tr><th>Cột 1</th><th>Cột 2</th><th>Cột 3</th></tr>
  </thead>
  <tbody>
    <tr><td>Dữ liệu</td><td>Dữ liệu</td><td>Dữ liệu</td></tr>
  </tbody>
</table>

<h2 id="ket-luan">Kết luận</h2>

<p>[Tóm tắt các điểm chính. Nhắc lại từ khóa chính.]</p>

<p>[CTA: Khuyến khích hành động cụ thể.]</p>

<blockquote>
  <p><strong>📌 Bạn thấy bài viết hữu ích?</strong> Hãy chia sẻ cho bạn bè hoặc khám phá thêm tại <a href="/kien-thuc">Kiến thức</a>.</p>
</blockquote>
```

### 5.2 JSON mẫu hoàn chỉnh — News

```json
{
  "title": "Học bổng DAAD 2026: Hướng dẫn đăng ký chi tiết",
  "excerpt": "Tìm hiểu điều kiện, hạn nộp và cách đăng ký học bổng DAAD 2026 dành cho sinh viên Việt Nam muốn du học Đức.",
  "content": "<p>Học bổng DAAD 2026 là cơ hội du học Đức miễn phí...</p>...<h2 id=\"ket-luan\">Kết luận</h2>...",
  "category": "du-hoc-duc",
  "is_published": true,
  "is_featured": false,
  "meta_title": "Học bổng DAAD 2026 — Đăng ký du học Đức | UnstressVN",
  "meta_description": "Hướng dẫn chi tiết cách đăng ký học bổng DAAD 2026 cho sinh viên Việt Nam. Điều kiện, hạn nộp, hồ sơ cần thiết. Đọc ngay!",
  "meta_keywords": "học bổng DAAD 2026, du học Đức miễn phí, điều kiện DAAD, đăng ký DAAD",
  "tags": "học bổng, DAAD, du học Đức, 2026",
  "cover_image_url": "https://example.com/daad-scholarship.jpg",
  "skip_seo_validation": false,
  "is_ai_generated": true,
  "ai_model": "gpt-4o",
  "workflow_id": "news-auto-publish",
  "source_url": "https://www.daad.de/scholarships/"
}
```

### 5.3 JSON mẫu — Knowledge

```json
{
  "title": "Ngữ pháp tiếng Đức A2: Perfekt — Thì quá khứ kép",
  "excerpt": "Hướng dẫn chi tiết cách dùng thì Perfekt trong tiếng Đức cho trình độ A2 với ví dụ thực tế.",
  "content": "<p>Thì Perfekt là thì quá khứ phổ biến nhất trong tiếng Đức...</p>...",
  "category": "ngu-phap",
  "language": "de",
  "level": "A2",
  "is_published": true,
  "meta_title": "Ngữ pháp Perfekt tiếng Đức A2 | UnstressVN",
  "meta_description": "Học thì Perfekt tiếng Đức A2: cách chia động từ, haben vs sein, ví dụ thực tế. Bài giảng chi tiết cho người mới.",
  "meta_keywords": "Perfekt tiếng Đức, quá khứ kép, ngữ pháp A2, haben sein",
  "tags": "Perfekt, ngữ pháp A2, tiếng Đức, haben sein",
  "is_ai_generated": true,
  "ai_model": "gpt-4o"
}
```

> **❗ Auto-tag:** Nếu `tags` để trống hoặc không gửi, API sẽ **tự động sinh tags** từ `title` + `category` + `meta_keywords` (tối đa 5 tags). Gửi `tags` nếu muốn kiểm soát chính xác.
```

### 5.4 JSON mẫu — Tool (article type)

```json
{
  "name": "Bảng chia động từ bất quy tắc tiếng Đức",
  "description": "Tra cứu nhanh bảng chia 100+ động từ bất quy tắc phổ biến nhất tiếng Đức.",
  "tool_type": "article",
  "content": "<p>Động từ bất quy tắc (unregelmäßige Verben)...</p>...",
  "category": "tu-dien",
  "language": "de",
  "icon": "book-open",
  "is_published": true,
  "meta_title": "Bảng động từ bất quy tắc tiếng Đức | UnstressVN",
  "meta_description": "Tra cứu bảng chia 100+ động từ bất quy tắc tiếng Đức phổ biến nhất. Cập nhật 2026.",
  "skip_seo_validation": false
}
```

### 5.5 JSON mẫu — Flashcard Deck

```json
{
  "name": "200 từ vựng B1 tiếng Đức — Chủ đề Beruf",
  "description": "Bộ từ vựng về nghề nghiệp, công việc cho trình độ B1",
  "language": "de",
  "level": "B1",
  "is_public": true,
  "cards": [
    {
      "front": "der Arbeitnehmer",
      "back": "người lao động",
      "example": "Der Arbeitnehmer hat einen Vertrag unterschrieben.",
      "pronunciation": "/ˈaʁbaɪ̯tˌneːmɐ/"
    },
    {
      "front": "die Bewerbung",
      "back": "đơn xin việc",
      "example": "Ich schreibe gerade eine Bewerbung.",
      "pronunciation": "/bəˈvɛʁbʊŋ/"
    }
  ]
}
```

### 5.6 JSON mẫu — Resource

```json
{
  "title": "Giáo trình Menschen A1 — PDF",
  "description": "Giáo trình Menschen A1 dành cho người mới bắt đầu học tiếng Đức. Bao gồm Kursbuch và Arbeitsbuch.",
  "category": "goethe",
  "resource_type": "pdf",
  "external_url": "https://drive.google.com/file/d/xxx/view",
  "author": "Hueber Verlag",
  "is_featured": true
}
```

### 5.7 JSON mẫu — Video

```json
{
  "youtube_id": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "title": "Phỏng vấn xin việc bằng tiếng Đức — Bewerbungsgespräch",
  "description": "Video hướng dẫn chuẩn bị phỏng vấn xin việc bằng tiếng Đức, dành cho trình độ B1-B2",
  "language": "de",
  "level": "B1",
  "is_featured": false
}
```

### 5.8 JSON mẫu — Stream Media (GDrive)

```json
{
  "title": "Phim Đức: Tschick (2016)",
  "description": "Phim Đức hay cho người học trình độ B1-B2. Câu chuyện về hai thiếu niên trong một chuyến road trip.",
  "storage_type": "gdrive",
  "gdrive_url": "https://drive.google.com/file/d/1ABC.../view",
  "category": "phim-duc",
  "language": "de",
  "level": "B1",
  "tags": "phim, Đức, road trip, B1",
  "is_public": true,
  "requires_login": false
}
```

---

## 6. API ENDPOINTS

### 6.1 Tổng quan — 22 endpoints

| # | Method | URL | Chức năng |
|---|--------|-----|-----------|
| 1 | GET | `/health/` | Health check (không cần auth) |
| 2 | GET | `/categories/?type=` | Danh sách categories |
| 3 | POST | `/categories/create/` | Tạo category mới |
| 4 | POST | `/news/` | Tạo bài tin tức |
| 5 | GET | `/news/list/` | Danh sách tin tức (paginated) |
| 6 | PUT/PATCH | `/news/<identifier>/` | Cập nhật tin tức |
| 7 | POST | `/knowledge/` | Tạo bài kiến thức |
| 8 | GET | `/knowledge/list/` | Danh sách kiến thức (paginated) |
| 9 | PUT/PATCH | `/knowledge/<identifier>/` | Cập nhật kiến thức |
| 10 | POST | `/tools/` | Tạo công cụ |
| 11 | GET | `/tools/list/` | Danh sách công cụ (paginated) |
| 12 | PUT/PATCH | `/tools/<identifier>/` | Cập nhật công cụ |
| 13 | POST | `/resources/` | Tạo tài liệu |
| 14 | GET | `/resources/list/` | Danh sách tài liệu (paginated) |
| 15 | PUT/PATCH | `/resources/<identifier>/` | Cập nhật tài liệu |
| 16 | POST | `/videos/` | Tạo video YouTube |
| 17 | GET | `/videos/list/` | Danh sách video (paginated) |
| 18 | POST | `/flashcards/` | Tạo bộ flashcard + thẻ |
| 19 | PUT/PATCH | `/flashcards/<identifier>/` | Cập nhật flashcard |
| 20 | POST | `/stream-media/` | Tạo video GDrive stream |
| 21 | DELETE | `/<type>/<identifier>/delete/` | Xoá nội dung (soft/hard) |
| 22 | POST | `/bulk/` | Tạo hàng loạt (max 50 items) |

### 6.2 Identifier lookup

Khi UPDATE hoặc DELETE, `<identifier>` có thể là:
- **slug** — ví dụ: `hoc-bong-daad-2026`
- **id** — ví dụ: `42`
- **source_id** — ví dụ: `reddit-abc123` (chỉ cho models có N8N tracking)
- **uid** — ví dụ: `a1b2c3d4-...` (chỉ cho StreamMedia)

### 6.3 LIST endpoints — Query params chung

| Param | Mô tả | Default |
|-------|-------|---------|
| `page` | Trang | 1 |
| `page_size` | Số item/trang | 20 (max: 100) |
| `search` | Tìm trong title/name | |
| `category` | Filter theo category slug | |
| `source` | Filter theo source (n8n, admin...) | |
| `is_published` | `true` / `false` | |

**Thêm cho Knowledge:** `language`, `level`
**Thêm cho Tools:** `tool_type`, `language`, `is_published`
**Thêm cho Resources:** `resource_type`
**Thêm cho Videos:** `language`, `level`

### 6.4 DELETE endpoint

```
DELETE /api/v1/n8n/<content_type>/<identifier>/delete/
```

**content_type:** `news`, `knowledge`, `resources`, `tools`, `videos`, `stream-media`, `flashcards`

- Mặc định: **Soft delete** (ẩn, không xoá)
- Thêm `?hard=true`: **Hard delete** (xoá vĩnh viễn, KHÔNG thể hoàn tác)

### 6.5 BULK endpoint

```
POST /api/v1/n8n/bulk/
```

```json
{
  "content_type": "news|knowledge|tools|resources|videos|flashcards|stream-media",
  "skip_seo_validation": true,
  "items": [ ...max 50 items... ]
}
```

Mỗi item cùng format như endpoint CREATE tương ứng. Auto dedup theo slug.

### 6.6 Image Pipeline

Áp dụng cho News, Knowledge, Tools, Resources khi tạo/cập nhật:

| Phương thức | Field | Mô tả |
|-------------|-------|-------|
| Upload file | `cover_image` | multipart/form-data |
| URL download | `cover_image_url` | Auto download → WebP → responsive |
| Placeholder | `auto_placeholder: true` | Tự tạo gradient image từ title |

Pipeline: Download → WebP → Thumbnail 400×267 → Responsive (480w, 768w, 1200w, 1920w) → og_image

---

## 7. HỆ THỐNG CATEGORIES

### 7.1 Lấy categories realtime

```bash
curl -H "X-API-Key: KEY" "https://unstressvn.com/api/v1/n8n/categories/?type=all"
```

### 7.2 Tạo category mới

```bash
curl -X POST -H "X-API-Key: KEY" -H "Content-Type: application/json" \
  "https://unstressvn.com/api/v1/n8n/categories/create/" \
  -d '{"type": "news", "name": "Du học Đức", "description": "Tin tức du học Đức"}'
```

### 7.3 Auto-create

Khi tạo bài viết, nếu `category` slug không tồn tại → API **tự động tạo** category mới.

### 7.4 Category types

| Type | Model | Dùng cho |
|------|-------|---------|
| `news` | news.Category | News Articles |
| `knowledge` | knowledge.Category | Knowledge Articles |
| `resources` | resources.Category | Resources |
| `tools` | tools.ToolCategory | Tools |
| `media` | mediastream.MediaCategory | Stream Media |

### 7.5 Categories THỰC TẾ trong Database (cập nhật 2026-02-28)

**News (30 bài):**
- `hoc-tieng-duc` — Học tiếng Đức (11 bài)
- `du-hoc` — Du học (7 bài)
- `hoc-tieng-anh` — Học tiếng Anh (6 bài)
- `thi-cu` — Thi cử (3 bài)
- `du-hoc-duc` — Du học Đức (1 bài)
- `kinh-nghiem` — Kinh nghiệm (1 bài)
- `doi-song-duc` — Đời sống Đức (1 bài)
- `tin-tuc-chung` — Tin tức chung
- `su-kien` — Sự kiện

**Knowledge (45 bài):**
- `ngu-phap` — Ngữ pháp (15 bài)
- `tu-vung` — Từ vựng (10 bài)
- `luyen-thi` — Luyện thi (7 bài)
- `bai-giang` — Bài giảng (5 bài)
- `ngu-phap-tieng-duc` — Ngữ pháp tiếng Đức (3 bài)
- `phat-am` — Phát âm (2 bài)
- `tu-vung-tieng-duc` — Từ vựng tiếng Đức (1 bài)
- `kinh-nghiem-du-hoc` — Kinh nghiệm du học (1 bài)
- `meo-hoc-ngoai-ngu` — Mẹo học ngoại ngữ (1 bài)
- `van-hoa` — Văn hóa
- `meo-hoc` — Mẹo học

**Tools (39 công cụ):**
- `tu-dien` — Từ điển (9)
- `luyen-tap` — Luyện tập (6)
- `hoc-tu-vung` — Học từ vựng (4)
- `dich-thuat` — Dịch thuật (4)
- `phat-am` — Phát âm (3)
- `luyen-nghe` — Luyện nghe (3)
- `phan-mem` — Phần mềm hỗ trợ (3)
- `ngu-phap` — Ngữ pháp (3)
- `flashcard` — Flashcard (2)
- `luyen-noi` — Luyện nói (2)

**Resources (24 tài liệu):**
- `tieng-duc` — Tiếng Đức (7)
- `ielts` — IELTS (6)
- `goethe` — Goethe (4)
- `tieng-anh` — Tiếng Anh (4)
- `tong-hop` — Tổng hợp (3)

**Stream Media (1 video):**
- `thu-gian` — Thư giãn (1)

> **Lưu ý:** Dùng `GET /api/v1/n8n/categories/?type=all` để lấy danh sách realtime.

---

## 8. SCRIPTS MẪU PYTHON — AUTOMATION

### 8.1 Script tạo bài News từ AI

```python
#!/usr/bin/env python3
"""
Script mẫu: Tạo bài viết News tự động bằng AI
Yêu cầu: pip install requests openai
"""
import requests
import json
from openai import OpenAI

# ============ CẤU HÌNH ============
API_URL = "https://unstressvn.com/api/v1/n8n"
API_KEY = "your-unstressvn-api-key"
OPENAI_KEY = "your-openai-api-key"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

# ============ AI TẠO NỘI DUNG ============
SYSTEM_PROMPT = """Bạn là chuyên gia viết bài SEO cho website UnstressVN — nền tảng học ngoại ngữ cho người Việt.

BẮT BUỘC:
1. Trả về JSON hợp lệ (KHÔNG markdown code block)
2. content phải ≥ 600 từ, HTML chuẩn
3. Tối thiểu 3 thẻ <h2 id="">, KHÔNG <h1>
4. Bắt đầu bằng <p> chứa từ khóa chính
5. Có danh sách <ul>/<ol>, <blockquote>, <h2 id="ket-luan">Kết luận</h2>
6. KHÔNG inline styles, KHÔNG <font>, <center>, <br>

Format JSON:
{
  "title": "40-65 ký tự, từ khóa chính ở đầu",
  "excerpt": "80-200 ký tự",
  "content": "HTML ≥ 600 từ",
  "meta_title": "50-60 ký tự — [Từ khóa] | UnstressVN",
  "meta_description": "120-155 ký tự + CTA",
  "meta_keywords": "3-7 keywords, comma-separated"
}"""

def generate_article(topic, category, main_keyword):
    """Dùng AI tạo nội dung bài viết"""
    client = OpenAI(api_key=OPENAI_KEY)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Viết bài TIN TỨC về: {topic}\nDanh mục: {category}\nTừ khóa chính: {main_keyword}\nĐộ dài: 1200+ từ"}
        ],
        temperature=0.7,
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)

def publish_news(article_data, category):
    """Đăng bài lên UnstressVN"""
    payload = {
        **article_data,
        "category": category,
        "is_published": True,
        "is_ai_generated": True,
        "ai_model": "gpt-4o",
        "auto_placeholder": True,
    }
    
    r = requests.post(f"{API_URL}/news/", headers=HEADERS, json=payload)
    return r.json()

# ============ CHẠY ============
if __name__ == "__main__":
    # 1. Tạo nội dung
    article = generate_article(
        topic="Học bổng Erasmus 2026 — Cơ hội du học châu Âu",
        category="hoc-bong",
        main_keyword="học bổng Erasmus 2026"
    )
    print(f"✅ AI tạo: {article['title']}")
    
    # 2. Đăng bài
    result = publish_news(article, category="hoc-bong")
    if result.get("success"):
        print(f"✅ Đăng thành công: {result['article']['url']}")
    else:
        print(f"❌ Lỗi: {result.get('error')}")
```

### 8.2 Script tạo Flashcard từ AI

```python
#!/usr/bin/env python3
"""
Script mẫu: Tạo bộ Flashcard từ vựng bằng AI
"""
import requests
import json
from openai import OpenAI

API_URL = "https://unstressvn.com/api/v1/n8n"
API_KEY = "your-unstressvn-api-key"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

FLASHCARD_PROMPT = """Tạo bộ flashcard từ vựng tiếng Đức.
Trả về JSON:
{
  "name": "Tên bộ flashcard",
  "description": "Mô tả ngắn",
  "cards": [
    {
      "front": "từ tiếng Đức (có mạo từ nếu là danh từ)",
      "back": "nghĩa tiếng Việt",
      "example": "Câu ví dụ tiếng Đức",
      "pronunciation": "phiên âm IPA"
    }
  ]
}"""

def generate_flashcards(topic, level, count=20):
    client = OpenAI(api_key="your-openai-key")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": FLASHCARD_PROMPT},
            {"role": "user", "content": f"Tạo {count} flashcard chủ đề '{topic}' cho trình độ {level}."}
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

def publish_flashcards(data, language="de", level="B1"):
    payload = {
        **data,
        "language": language,
        "level": level,
        "is_public": True,
    }
    r = requests.post(f"{API_URL}/flashcards/", headers=HEADERS, json=payload)
    return r.json()

if __name__ == "__main__":
    data = generate_flashcards("Essen und Trinken (Ẩm thực)", "B1", count=30)
    result = publish_flashcards(data, "de", "B1")
    if result.get("success"):
        print(f"✅ Tạo {result.get('cards_created', 0)} thẻ: {result['deck']['slug']}")
    else:
        print(f"❌ Lỗi: {result.get('error')}")
```

### 8.3 Script Bulk import từ CSV

```python
#!/usr/bin/env python3
"""
Script mẫu: Bulk import bài viết từ CSV
CSV format: title,content,category,language,level
"""
import csv
import requests

API_URL = "https://unstressvn.com/api/v1/n8n"
API_KEY = "your-api-key"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

def bulk_import(csv_file, content_type="knowledge"):
    items = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            items.append({
                "title": row["title"],
                "content": row["content"],
                "category": row.get("category", ""),
                "language": row.get("language", "all"),
                "level": row.get("level", "all"),
                "is_published": True,
                "skip_seo_validation": True,
            })
    
    # Split into batches of 50
    for i in range(0, len(items), 50):
        batch = items[i:i+50]
        payload = {
            "content_type": content_type,
            "skip_seo_validation": True,
            "items": batch,
        }
        r = requests.post(f"{API_URL}/bulk/", headers=HEADERS, json=payload)
        result = r.json()
        print(f"Batch {i//50 + 1}: created={result.get('created')}, skipped={result.get('skipped')}, failed={result.get('failed')}")

if __name__ == "__main__":
    bulk_import("articles.csv", "knowledge")
```

### 8.4 Script kiểm tra và liệt kê nội dung

```python
#!/usr/bin/env python3
"""
Script: Kiểm tra nội dung hiện có trên website
"""
import requests

API_URL = "https://unstressvn.com/api/v1/n8n"
API_KEY = "your-api-key"
HEADERS = {"X-API-Key": API_KEY}

def list_content(content_type, **filters):
    params = {"page_size": 100, **filters}
    r = requests.get(f"{API_URL}/{content_type}/list/", headers=HEADERS, params=params)
    data = r.json()
    print(f"\n{'='*50}")
    print(f"{content_type.upper()}: {data['total']} bài")
    print(f"{'='*50}")
    for item in data.get("results", []):
        title = item.get("title") or item.get("name", "?")
        slug = item.get("slug", "?")
        print(f"  [{item['id']}] {title} → /{slug}")
    return data

def list_categories():
    r = requests.get(f"{API_URL}/categories/", headers=HEADERS, params={"type": "all"})
    data = r.json()
    print(f"\nCATEGORIES:")
    for cat in data.get("categories", []):
        print(f"  [{cat['type']}] {cat['name']} → {cat['slug']}")

if __name__ == "__main__":
    list_categories()
    for ct in ["news", "knowledge", "tools", "resources", "videos"]:
        list_content(ct)
```

---

## 9. PROMPTS AI

### 9.1 System Prompt — Tạo bài viết (đầy đủ)

```
Bạn là chuyên gia viết bài SEO cho website UnstressVN (unstressvn.com) — nền tảng học ngoại ngữ (tiếng Đức, tiếng Anh) cho người Việt Nam.

═══ QUY TẮC BẮT BUỘC ═══

1. NGÔN NGỮ: Tiếng Việt, giọng văn thân thiện, chuyên nghiệp, dễ hiểu.

2. CẤU TRÚC HTML cho "content":
   a) Đoạn mở đầu: <p>Từ khóa chính... mô tả + lợi ích đọc bài.</p>
   b) Mục lục (bài > 800 từ): <nav><h2>Nội dung bài viết</h2><ul>...</ul></nav><hr>
   c) Sections: ≥ 3 thẻ <h2 id="..."> chứa từ khóa phụ
   d) Đoạn văn: <p>3-5 câu, topic sentence đầu đoạn</p>
   e) Danh sách: ≥ 1 <ul>/<ol>
   f) Tips: ≥ 1 <blockquote>
   g) Kết luận: <h2 id="ket-luan">Kết luận</h2> + CTA

3. CẤM: <h1>, inline styles, <br>, <font>, <center>, <b>, <i>, JavaScript

4. SEO:
   - title: 40-65 ký tự
   - meta_title: 50-60 ký tự, format "[Từ khóa] | UnstressVN"
   - meta_description: 120-155 ký tự + CTA
   - excerpt: 80-200 ký tự
   - meta_keywords: 3-7 keywords
   - content: ≥ 600 từ (tối ưu 1200-2000)

5. FORMAT trả về — JSON thuần (KHÔNG markdown):
{
  "title": "...",
  "excerpt": "...",
  "content": "HTML chuẩn",
  "meta_title": "...",
  "meta_description": "...",
  "meta_keywords": "..."
}
```

### 9.2 User Prompt — News

```
Viết bài TIN TỨC cho website UnstressVN.
Chủ đề: [CHỦ ĐỀ]
Danh mục: [CATEGORY SLUG]
Từ khóa chính: [TỪ KHÓA]
Từ khóa phụ: [TỪ KHÓA PHỤ 1], [TỪ KHÓA PHỤ 2]
Độ dài: 1200-1500 từ
```

### 9.3 User Prompt — Knowledge

```
Viết bài KIẾN THỨC cho website UnstressVN.
Chủ đề: [CHỦ ĐỀ]
Ngôn ngữ: [de/en]
Trình độ: [A1/A2/B1/B2/C1/C2]
Từ khóa chính: [TỪ KHÓA]
Độ dài: 1500-2000 từ
Yêu cầu: Thêm ví dụ thực tế bằng ngôn ngữ học, giải nghĩa từ vựng khó.
```

### 9.4 User Prompt — Flashcard

```
Tạo bộ flashcard từ vựng tiếng Đức.
Chủ đề: [CHỦ ĐỀ]
Trình độ: [LEVEL]
Số lượng: [20-50] thẻ
Yêu cầu: Mỗi thẻ có front (từ tiếng Đức + mạo từ), back (nghĩa Việt), example (câu ví dụ), pronunciation (IPA).
```

---

## 10. N8N WORKFLOWS MẪU

### 10.1 Workflow: Tự động đăng tin tức hàng ngày

```
Schedule (8:00 AM) → Google Sheets (đọc topics) → OpenAI (tạo bài)
→ Code (parse JSON) → HTTP Request (POST /news/) → IF (success?)
→ [YES] Google Sheets (status=published) + Telegram (thông báo)
→ [NO] Telegram (cảnh báo lỗi)
```

### 10.2 Workflow: RSS → Knowledge tự động

```
RSS Feed → Extract Content → OpenAI (rewrite theo SEO template)
→ HTTP Request (POST /knowledge/) → Telegram notification
```

### 10.3 Workflow: Tạo flashcard từ AI hàng tuần

```
Schedule (MON 10:00) → OpenAI (tạo 30 flashcards chủ đề random)
→ HTTP Request (POST /flashcards/) → Telegram
```

### 10.4 Workflow: Google Drive → Stream

```
Google Drive Trigger (new file) → Get File Info
→ HTTP Request (POST /stream-media/) → Telegram
```

### 10.5 N8N HTTP Request Node cấu hình

```
Method: POST
URL: https://unstressvn.com/api/v1/n8n/news/
Authentication: Header Auth
  - Name: X-API-Key
  - Value: {{$env.UNSTRESSVN_API_KEY}}
Content-Type: application/json
Body: {{$json}}
```

---

## 11. XỬ LÝ LỖI

### ⚡ Field Auto-Truncation (v2026-02-28)

API **tự động cắt ngắn** các trường CharField vượt quá giới hạn DB thay vì crash:

| Field | Max | Hành vi |
|-------|-----|--------|
| `title` / `name` | 200-255 | Auto-truncate, không lỗi |
| `meta_title` | 70 | Auto-truncate |
| `meta_description` | 160 | Auto-truncate |
| `meta_keywords` | 255 | Auto-truncate |
| `excerpt` | 500 | Auto-truncate |
| `source_url` | 200 | Auto-truncate |
| `ai_model` | 50 | Auto-truncate |
| `n8n_workflow_id` | 50 | Auto-truncate |
| `n8n_execution_id` | 100 | Auto-truncate |

> **Lưu ý:** Dữ liệu bị cắt sẽ mất phần cuối. Nên kiểm soát độ dài từ phía AI/n8n để tránh mất nội dung.

### Status codes

| Code | Ý nghĩa | Xử lý |
|------|---------|--------|
| 200 | OK (update, list, skip duplicate) | Tiếp tục |
| 201 | Created | Thành công |
| 400 | Bad request (thiếu field, SEO fail) | Kiểm tra body |
| 403 | API Key sai hoặc hết hạn | Kiểm tra header `X-API-Key` |
| 404 | Không tìm thấy | Kiểm tra identifier |
| 500 | Server error | JSON chi tiết, thử lại sau 5 phút |

> **Quan trọng (v2026-02-28):** Tất cả lỗi đều trả về **JSON** (không bao giờ trả HTML).
> Kể cả lỗi 500 cũng có `success`, `error`, `hint` trong JSON response.

### Error response format

**Lỗi validation (400):**
```json
{
  "success": false,
  "error": "Mô tả lỗi tiếng Việt",
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

**Lỗi server (500) — luôn trả JSON:**
```json
{
  "success": false,
  "error": "ValueError: Chi tiết lỗi...",
  "hint": "Lỗi hệ thống không mong muốn. Kiểm tra dữ liệu gửi và thử lại.",
  "path": "/api/v1/n8n/news/"
}
```

**Lỗi tạo object (500 — có hint chi tiết):**
```json
{
  "success": false,
  "error": "Lỗi tạo bài viết: DataError: value too long...",
  "hint": "Kiểm tra dữ liệu gửi từ n8n — có thể trường quá dài hoặc dữ liệu không hợp lệ"
}
```

### Duplicate detection (auto skip)

API tự động phát hiện trùng lặp và trả 200 + `"action": "skipped"`:
- News/Knowledge: theo `slug`
- Video: theo `youtube_id` + `source_id`
- Flashcard: theo `name + language + level`
- StreamMedia: theo `gdrive_url`

### Retry logic (Python)

```python
import time

def api_call_with_retry(url, data, max_retries=3):
    for attempt in range(max_retries):
        try:
            r = requests.post(url, headers=HEADERS, json=data, timeout=30)
            if r.status_code in [200, 201]:
                return r.json()
            elif r.status_code == 400:
                return r.json()  # Don't retry client errors
            elif r.status_code >= 500:
                time.sleep(5 * (attempt + 1))  # Backoff
                continue
        except requests.exceptions.Timeout:
            time.sleep(5 * (attempt + 1))
            continue
    return {"success": False, "error": "Max retries exceeded"}
```

---

## 12. XOÁ DỮ LIỆU MẪU

### Django Management Command

```bash
# Xem dữ liệu mẫu (dry-run, không xoá)
python manage.py cleanup_sample_data --dry-run

# Xoá tất cả dữ liệu mẫu
python manage.py cleanup_sample_data --all --confirm

# Xoá theo loại
python manage.py cleanup_sample_data --type news --confirm
python manage.py cleanup_sample_data --type knowledge --confirm
python manage.py cleanup_sample_data --type tools --confirm
python manage.py cleanup_sample_data --type resources --confirm
python manage.py cleanup_sample_data --type videos --confirm
python manage.py cleanup_sample_data --type flashcards --confirm
python manage.py cleanup_sample_data --type stream-media --confirm
python manage.py cleanup_sample_data --type categories --confirm
python manage.py cleanup_sample_data --type users --confirm
python manage.py cleanup_sample_data --type navigation --confirm

# Xoá đồng thời nhiều loại
python manage.py cleanup_sample_data --type news --type knowledge --type tools --confirm
```

### Qua API (DELETE endpoint)

```python
# Xoá 1 bài viết (soft delete)
requests.delete(f"{API_URL}/news/{slug}/delete/", headers=HEADERS)

# Xoá vĩnh viễn
requests.delete(f"{API_URL}/news/{slug}/delete/?hard=true", headers=HEADERS)
```

---

## PHỤ LỤC

### A. Checklist trước khi đăng bài

```
☐ title: 40-65 ký tự, từ khóa chính ở đầu
☐ content: ≥ 600 từ
☐ content: ≥ 3 thẻ <h2 id="">
☐ content: Không <h1>, không inline styles
☐ content: Bắt đầu bằng <p> chứa từ khóa
☐ content: ≥ 1 danh sách, ≥ 1 blockquote
☐ content: <h2 id="ket-luan">Kết luận</h2> + CTA
☐ excerpt: 80-200 ký tự
☐ meta_title: 50-60 ký tự
☐ meta_description: 120-155 ký tự
☐ meta_keywords: 3-7 từ khóa
☐ category: slug hợp lệ
☐ cover_image_url hoặc auto_placeholder: true
```

### B. Các link nội bộ phổ biến (dùng trong content)

```html
<a href="/tin-tuc">Tin tức</a>
<a href="/kien-thuc">Kiến thức</a>
<a href="/tai-lieu">Tài liệu</a>
<a href="/video">Video</a>
<a href="/cong-cu">Công cụ</a>
<a href="/stream">Media Stream</a>
```

### C. File liên quan

| File | Mô tả |
|------|-------|
| `docs/SEO_CONTENT_TEMPLATE.md` | Template HTML chi tiết |
| `docs/N8N_AUTO_PUBLISH_GUIDE.md` | Hướng dẫn N8N workflow |
| `api/N8N_API_DOCUMENTATION.md` | API reference đầy đủ |
| `docs/DATABASE_SCHEMA.md` | Database schema |
| `docs/MEDIA_STREAM.md` | Hướng dẫn media streaming |
