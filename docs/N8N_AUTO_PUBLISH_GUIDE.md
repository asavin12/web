# 🤖 HƯỚNG DẪN TỰ ĐỘNG ĐĂNG BÀI VỚI N8N — UnstressVN

> Tài liệu hướng dẫn chi tiết cách thiết lập n8n workflow để tự động tạo bài viết
> theo **form chuẩn SEO bắt buộc** của UnstressVN.

---

## MỤC LỤC

1. [Tổng quan hệ thống](#1-tổng-quan-hệ-thống)
2. [Chuẩn bị môi trường](#2-chuẩn-bị-môi-trường)
3. [Cấu trúc HTML bắt buộc](#3-cấu-trúc-html-bắt-buộc)
4. [Workflow 1: Đăng bài Tin tức](#4-workflow-1-đăng-bài-tin-tức-news)
5. [Workflow 2: Đăng bài Kiến thức](#5-workflow-2-đăng-bài-kiến-thức-knowledge)
6. [Workflow 3: Đăng tài liệu](#6-workflow-3-đăng-tài-liệu-resource)
7. [Workflow 4: Đăng video](#7-workflow-4-đăng-video)
8. [Prompt AI tạo nội dung chuẩn SEO](#8-prompt-ai-tạo-nội-dung-chuẩn-seo)
9. [Xử lý lỗi và debug](#9-xử-lý-lỗi-và-debug)
10. [Danh sách Categories có sẵn](#10-danh-sách-categories)

---

## 1. TỔNG QUAN HỆ THỐNG

### Kiến trúc

```
[Nguồn nội dung]  →  [n8n Workflow]  →  [AI xử lý/tạo nội dung]  →  [UnstressVN API]  →  [Website]
   (RSS/Sheets/       (Xử lý logic)      (GPT-4o/Claude)           (POST /api/v1/n8n/)    (Hiển thị)
    Manual/AI)
```

### Các endpoint API

| Endpoint | Method | Chức năng |
|----------|--------|-----------|
| `/api/v1/n8n/health/` | GET | Kiểm tra API hoạt động (không cần auth) |
| `/api/v1/n8n/categories/?type=news` | GET | Lấy danh sách categories |
| `/api/v1/n8n/news/` | POST | Tạo bài viết Tin tức |
| `/api/v1/n8n/knowledge/` | POST | Tạo bài viết Kiến thức |
| `/api/v1/n8n/resources/` | POST | Tạo tài liệu |
| `/api/v1/n8n/videos/` | POST | Tạo video |

### Xác thực

Mọi request (trừ health check) cần header:
```
X-API-Key: <API_KEY_CỦA_BẠN>
```

---

## 2. CHUẨN BỊ MÔI TRƯỜNG

### Bước 1: Kiểm tra API hoạt động

Trong n8n, tạo **HTTP Request** node:

```
Method: GET
URL: https://unstressvn.com/api/v1/n8n/health/
```

Kết quả mong đợi:
```json
{
  "status": "ok",
  "service": "UnstressVN API",
  "version": "1.0.0"
}
```

### Bước 2: Tạo Credentials trong n8n

1. Vào **Settings → Credentials → Add Credential**
2. Chọn **Header Auth**
3. Cấu hình:
   - **Name:** `UnstressVN API Key`
   - **Header Name:** `X-API-Key`
   - **Header Value:** `<API_KEY_CỦA_BẠN>`

### Bước 3: Lấy danh sách Categories

Tạo HTTP Request node để lấy categories:
```
Method: GET
URL: https://unstressvn.com/api/v1/n8n/categories/?type=all
Headers: X-API-Key: <API_KEY>
```

---

## 3. CẤU TRÚC HTML BẮT BUỘC

> ⚠️ **QUAN TRỌNG:** Mọi nội dung bài viết (`content`) PHẢI tuân thủ cấu trúc HTML dưới đây.
> Tham khảo chi tiết tại file `docs/SEO_CONTENT_TEMPLATE.md`.

### Cấu trúc tối thiểu cho mỗi bài viết:

```html
<!-- 1. Đoạn mở đầu (BẮT BUỘC) — Chứa từ khóa chính -->
<p>[Đoạn mở đầu 2-3 câu, từ khóa chính ở câu đầu]</p>

<!-- 2. Mục lục (KHUYẾN NGHỊ cho bài > 800 từ) -->
<nav>
  <h2>Nội dung bài viết</h2>
  <ul>
    <li><a href="#phan-1">1. [Tiêu đề]</a></li>
    <li><a href="#phan-2">2. [Tiêu đề]</a></li>
    <li><a href="#ket-luan">Kết luận</a></li>
  </ul>
</nav>

<hr>

<!-- 3. Các section nội dung (BẮT BUỘC ≥ 3 thẻ H2) -->
<h2 id="phan-1">1. [Tiêu đề chứa từ khóa phụ]</h2>
<p>[Nội dung 3-5 câu/đoạn]</p>

<!-- 4. Danh sách (BẮT BUỘC ≥ 1) -->
<ul>
  <li><strong>[Điểm chính]:</strong> [Giải thích]</li>
</ul>

<!-- 5. Tips/Lưu ý (KHUYẾN NGHỊ ≥ 1) -->
<blockquote>
  <p><strong>💡 Mẹo:</strong> [Thông tin hữu ích]</p>
</blockquote>

<!-- 6. Kết luận + CTA (BẮT BUỘC) -->
<h2 id="ket-luan">Kết luận</h2>
<p>[Tóm tắt + từ khóa chính]</p>
<blockquote>
  <p><strong>📌 Bạn thấy hữu ích?</strong> Chia sẻ hoặc khám phá thêm tại <a href="/kien-thuc">Kiến thức</a>.</p>
</blockquote>
```

### Quy tắc nhanh:

| Yếu tố | Yêu cầu |
|---------|---------|
| Độ dài tối thiểu | ≥ 600 từ |
| Đoạn mở đầu | Bắt buộc, chứa từ khóa chính |
| Số H2 | Tối thiểu 3 |
| H2 id | Bắt buộc cho anchor link |
| Danh sách | Tối thiểu 1 (ul hoặc ol) |
| Kết luận | Bắt buộc H2 + CTA |
| Link nội bộ | Tối thiểu 1 |
| KHÔNG dùng H1 | Đã có title, dùng H1 là sai SEO |

---

## 4. WORKFLOW 1: ĐĂNG BÀI TIN TỨC (News)

### Sơ đồ workflow

```
[Trigger]  →  [AI Tạo nội dung]  →  [Validate]  →  [POST API]  →  [Notify]
```

### Bước 1: Trigger Node

Chọn 1 trong các trigger:

**a) Schedule Trigger (Chạy tự động theo lịch):**
```
Cron: 0 8 * * 1,3,5    (8:00 sáng thứ 2, 4, 6)
```

**b) Webhook Trigger (Chạy khi nhận request):**
```
Method: POST
Path: /webhook/create-news
```

**c) Google Sheets Trigger (Khi có dòng mới):**
```
Sheet ID: <ID_Google_Sheet>
Sheet Name: "Bài viết"
Trigger: On new row
```

### Bước 2: AI Node — Tạo nội dung chuẩn SEO

Dùng **OpenAI** hoặc **HTTP Request** node gọi AI.

**System Prompt cho AI (copy nguyên văn):**

```
Bạn là chuyên gia viết bài SEO cho website UnstressVN — một nền tảng học ngoại ngữ (tiếng Đức, tiếng Anh) dành cho người Việt.

BẮT BUỘC tuân thủ CẤU TRÚC HTML sau cho trường "content":

1. ĐOẠN MỞ ĐẦU (BẮT BUỘC):
   - Dùng thẻ <p>, chứa từ khóa chính ngay câu đầu tiên
   - 2-3 câu giới thiệu vấn đề + lợi ích đọc bài

2. MỤC LỤC (cho bài > 800 từ):
   <nav><h2>Nội dung bài viết</h2><ul><li><a href="#id">Tiêu đề</a></li></ul></nav>
   Theo sau bởi <hr>

3. SECTIONS NỘI DUNG:
   - Tối thiểu 3 thẻ <h2 id="..."> với anchor ID
   - Mỗi H2 chứa từ khóa phụ
   - Đoạn văn 3-5 câu trong <p>
   - Ít nhất 1 danh sách <ul> hoặc <ol>
   - Ít nhất 1 <blockquote> cho tips/lưu ý
   - Dùng <strong> cho điểm nhấn
   - Dùng <table> cho so sánh

4. KẾT LUẬN (BẮT BUỘC):
   <h2 id="ket-luan">Kết luận</h2>
   - Tóm tắt + nhắc lại từ khóa chính
   - CTA trong <blockquote>

KHÔNG ĐƯỢC DÙNG: <h1>, inline styles, <br>, <div style>, <font>, <b>, <i>

Trả về JSON với cấu trúc:
{
  "title": "40-65 ký tự, từ khóa chính ở đầu",
  "excerpt": "80-200 ký tự, tóm tắt giá trị bài viết",
  "content": "HTML theo cấu trúc trên, ≥ 600 từ",
  "meta_title": "50-60 ký tự — [Từ khóa] | UnstressVN",
  "meta_description": "120-155 ký tự, từ khóa + CTA",
  "meta_keywords": "3-7 từ khóa, cách nhau dấu phẩy"
}
```

**User Prompt mẫu:**
```
Viết bài tin tức về chủ đề: [CHỦ ĐỀ]
Danh mục: [CATEGORY SLUG, VD: hoc-tieng-duc]
Từ khóa chính: [TỪ KHÓA CHÍNH]
Từ khóa phụ: [TỪ KHÓA PHỤ 1], [TỪ KHÓA PHỤ 2]
Ngôn ngữ bài viết: Tiếng Việt
Độ dài: 1200-1500 từ
```

### Bước 3: Set Node — Chuẩn bị dữ liệu

Map dữ liệu từ AI response sang format API:

```javascript
// Expression trong Set node
{
  "title": {{ $json.title }},
  "content": {{ $json.content }},
  "excerpt": {{ $json.excerpt }},
  "category": "hoc-tieng-duc",
  "is_featured": false,
  "is_published": true,
  "meta_title": {{ $json.meta_title }},
  "meta_description": {{ $json.meta_description }},
  "meta_keywords": {{ $json.meta_keywords }},
  "is_ai_generated": true,
  "ai_model": "gpt-4o",
  "workflow_id": "news_auto_publish",
  "execution_id": {{ $execution.id }}
}
```

### Bước 4: HTTP Request — Gửi API

```
Method: POST
URL: https://unstressvn.com/api/v1/n8n/news/
Authentication: Header Auth (UnstressVN API Key)
Content-Type: application/json
Body: {{ $json }} (từ node trước)
```

### Bước 5: IF Node — Kiểm tra kết quả

```javascript
// Điều kiện thành công
{{ $json.success }} === true
```

**Nhánh thành công:** Gửi notification (Telegram/Email)
**Nhánh thất bại:** Log lỗi + gửi cảnh báo

---

## 5. WORKFLOW 2: ĐĂNG BÀI KIẾN THỨC (Knowledge)

Tương tự Workflow 1, nhưng cần thêm các trường:

### Endpoint
```
POST https://unstressvn.com/api/v1/n8n/knowledge/
```

### Body bổ sung so với News

```json
{
  "language": "de",
  "level": "B1"
}
```

### Giá trị `language` hợp lệ:
| Giá trị | Ý nghĩa |
|---------|---------|
| `de` | Tiếng Đức |
| `en` | Tiếng Anh |
| `all` | Tất cả ngôn ngữ (mặc định) |

### Giá trị `level` hợp lệ:
| Giá trị | Ý nghĩa |
|---------|---------|
| `A1` | Sơ cấp |
| `A2` | Sơ trung |
| `B1` | Trung cấp |
| `B2` | Trung cao |
| `C1` | Cao cấp |
| `C2` | Thành thạo |
| `all` | Mọi trình độ (mặc định) |

### Prompt bổ sung cho AI:
Thêm vào system prompt:
```
Khi viết bài Kiến thức, bổ sung thêm:
- Ví dụ thực tế bằng ngôn ngữ đang học (tiếng Đức/Anh)
- Phiên âm hoặc giải nghĩa cho từ vựng khó
- Bài tập nhỏ hoặc câu hỏi kiểm tra ở cuối (nếu phù hợp)
```

---

## 6. WORKFLOW 3: ĐĂNG TÀI LIỆU (Resource)

### Endpoint
```
POST https://unstressvn.com/api/v1/n8n/resources/
```

### Body

```json
{
  "title": "Tên tài liệu (BẮT BUỘC)",
  "description": "Mô tả tài liệu (BẮT BUỘC)",
  "category": "slug-category",
  "resource_type": "ebook",
  "external_url": "https://drive.google.com/...",
  "youtube_url": "https://youtube.com/...",
  "author": "Tên tác giả",
  "is_featured": false,
  "workflow_id": "resource_auto",
  "execution_id": "exec_123"
}
```

### Giá trị `resource_type` hợp lệ:
| Giá trị | Ý nghĩa |
|---------|---------|
| `ebook` | Sách điện tử |
| `book` | Sách |
| `pdf` | Tài liệu PDF |
| `audio` | Tài liệu nghe |
| `video` | Video |
| `document` | Tài liệu chung (mặc định) |
| `flashcard` | Flashcard |

---

## 7. WORKFLOW 4: ĐĂNG VIDEO

### Endpoint
```
POST https://unstressvn.com/api/v1/n8n/videos/
```

### Body

```json
{
  "youtube_id": "dQw4w9WgXcQ",
  "title": "Tiêu đề video (tùy chọn — tự lấy từ YouTube nếu bỏ trống)",
  "description": "Mô tả video",
  "language": "de",
  "level": "A2",
  "is_featured": false,
  "workflow_id": "video_auto",
  "execution_id": "exec_456"
}
```

> **Lưu ý:** `youtube_id` có thể là ID thuần (`dQw4w9WgXcQ`) hoặc URL đầy đủ (`https://www.youtube.com/watch?v=dQw4w9WgXcQ`). API sẽ tự trích xuất ID.

> **Chống trùng lặp:** API tự động kiểm tra trùng bằng `youtube_id` và `source_id`. Nếu video đã tồn tại, trả về `"action": "skipped"`.

---

## 8. PROMPT AI TẠO NỘI DUNG CHUẨN SEO

### 8.1. System Prompt đầy đủ (Copy vào n8n)

```
Bạn là chuyên gia viết bài SEO cho website UnstressVN (unstressvn.com) — nền tảng học ngoại ngữ (tiếng Đức, tiếng Anh) cho người Việt Nam.

═══ QUY TẮC BẮT BUỘC ═══

1. NGÔN NGỮ: Viết bằng tiếng Việt, giọng văn thân thiện, chuyên nghiệp, dễ hiểu.

2. CẤU TRÚC HTML BẮT BUỘC cho trường "content":

   a) ĐOẠN MỞ ĐẦU (BẮT BUỘC):
      <p>[Từ khóa chính trong câu đầu]. [2-3 câu mô tả + lợi ích đọc bài].</p>

   b) MỤC LỤC (cho bài > 800 từ):
      <nav>
        <h2>Nội dung bài viết</h2>
        <ul>
          <li><a href="#section-id">Tiêu đề</a></li>
        </ul>
      </nav>
      <hr>

   c) SECTIONS NỘI DUNG (tối thiểu 3 thẻ H2):
      <h2 id="section-id">Tiêu đề chứa từ khóa phụ</h2>
      <p>Nội dung 3-5 câu. Topic sentence ở đầu đoạn.</p>
      - Dùng <h3> cho mục con
      - Dùng <ul>/<ol> cho danh sách (tối thiểu 1)
      - Dùng <blockquote> cho tips/lưu ý (tối thiểu 1)
      - Dùng <strong> cho điểm nhấn
      - Dùng <table> cho so sánh
      - Dùng <a href="/..."> cho liên kết nội bộ (tối thiểu 1)

   d) KẾT LUẬN (BẮT BUỘC):
      <h2 id="ket-luan">Kết luận</h2>
      <p>Tóm tắt + nhắc lại từ khóa chính.</p>
      <blockquote><p><strong>📌 CTA</strong> Kêu gọi hành động.</p></blockquote>

3. KHÔNG ĐƯỢC DÙNG:
   - <h1> (title đã là H1)
   - Inline styles (style="...")
   - <br> thay cho <p>
   - <div>, <span>, <font>, <center>, <b>, <i>
   - JavaScript

4. SEO:
   - title: 40-65 ký tự, từ khóa chính ở đầu
   - meta_title: 50-60 ký tự, format "[Từ khóa] | UnstressVN"
   - meta_description: 120-155 ký tự, chứa từ khóa + CTA
   - excerpt: 80-200 ký tự
   - meta_keywords: 3-7 từ khóa, dấu phẩy ngăn cách
   - Mật độ từ khóa chính: 1-2%

5. ĐỘ DÀI: content ≥ 600 từ (tối ưu 1200-2000 từ)

═══ FORMAT TRẢ VỀ ═══

Trả về JSON hợp lệ (không có markdown code block):
{
  "title": "...",
  "excerpt": "...",
  "content": "...",
  "meta_title": "...",
  "meta_description": "...",
  "meta_keywords": "..."
}
```

### 8.2. User Prompt theo loại bài

**Tin tức:**
```
Viết bài TIN TỨC cho website UnstressVN.
Chủ đề: {{topic}}
Danh mục: {{category}}
Từ khóa chính: {{main_keyword}}
Từ khóa phụ: {{secondary_keywords}}
Độ dài: 1200-1500 từ
```

**Kiến thức:**
```
Viết bài KIẾN THỨC cho website UnstressVN.
Chủ đề: {{topic}}
Ngôn ngữ học: {{language}} (de/en)
Trình độ: {{level}} (A1-C2)
Từ khóa chính: {{main_keyword}}
Từ khóa phụ: {{secondary_keywords}}
Độ dài: 1500-2000 từ
Yêu cầu bổ sung: Thêm ví dụ bằng {{language}}, giải nghĩa từ vựng khó.
```

---

## 9. XỬ LÝ LỖI VÀ DEBUG

### ⚡ Field Auto-Truncation (mới)

API tự động cắt ngắn các trường vượt giới hạn để tránh lỗi:
- `title`: max 255 ký tự
- `meta_title`: max 70 ký tự
- `meta_description`: max 160 ký tự
- `excerpt`: max 500 ký tự

> Nên kiểm soát độ dài từ phía AI prompt để không bị cắt mất nội dung.

### Mã lỗi API

| HTTP Code | Ý nghĩa | Cách xử lý |
|-----------|---------|-------------|
| 200 | Thành công | Tiếp tục workflow |
| 201 | Tạo thành công | Tiếp tục workflow |
| 400 | Thiếu trường / SEO không đạt | Kiểm tra title, content, gửi `skip_seo_validation: true` |
| 403 | API Key không hợp lệ hoặc hết hạn | Kiểm tra lại X-API-Key |
| 404 | Không tìm thấy (update/delete) | Kiểm tra identifier |
| 500 | Lỗi server (JSON chi tiết) | Đọc `error` + `hint` trong response, thử lại |

> **Tất cả lỗi đều trả JSON** (không bao giờ HTML). Response luôn có `{"success": false, "error": "..."}`. 

### Kiểm tra response

Trong n8n, sau HTTP Request node, thêm **IF** node:

```javascript
// Kiểm tra thành công
Condition: {{ $json.success }} equals true

// Nhánh FALSE → Error handling
```

### Debug checklist

```
☐ API Key đúng trong header X-API-Key?
☐ Content-Type là application/json?
☐ Body là JSON hợp lệ (không có trailing comma)?
☐ Trường "title" có giá trị?
☐ Trường "content" có giá trị?
☐ Category slug tồn tại? (dùng GET categories để kiểm tra)
☐ Language hợp lệ? (de/en/all)
☐ Level hợp lệ? (A1/A2/B1/B2/C1/C2/all)
```

### Log lỗi trong n8n

Thêm **Error Trigger** node ở cuối workflow để bắt mọi lỗi:
```
On error: Continue (using error output)
```

---

## 10. DANH SÁCH CATEGORIES

### Lấy categories realtime

```
GET https://unstressvn.com/api/v1/n8n/categories/?type=all
Headers: X-API-Key: <API_KEY>
```

### Categories phổ biến (tham khảo)

**News:**
| Slug | Tên |
|------|-----|
| `hoc-tieng-duc` | Học tiếng Đức |
| `du-hoc-duc` | Du học Đức |
| `hoc-tieng-anh` | Học tiếng Anh |
| `tin-tuc-tong-hop` | Tin tức tổng hợp |

**Knowledge:**
| Slug | Tên |
|------|-----|
| `ngu-phap` | Ngữ pháp |
| `tu-vung` | Từ vựng |
| `ky-nang-nghe` | Kỹ năng nghe |
| `ky-nang-noi` | Kỹ năng nói |

> **Lưu ý:** Nếu gửi slug category không tồn tại, API sẽ **tự động tạo** category mới với tên = slug.

---

## PHỤ LỤC: WORKFLOW MẪU HOÀN CHỈNH

### Workflow: Tự động đăng bài Tin tức hàng ngày

```
1. [Schedule Trigger]     → Chạy 8:00 sáng mỗi ngày
      ↓
2. [Google Sheets]        → Đọc dòng chưa xử lý (cột "status" = "pending")
      ↓
3. [OpenAI / Claude]      → Tạo nội dung chuẩn SEO từ chủ đề
      ↓
4. [Code Node]            → Parse JSON response từ AI
      ↓
5. [Set Node]             → Map dữ liệu + thêm category, workflow_id
      ↓
6. [HTTP Request]         → POST /api/v1/n8n/news/
      ↓
7. [IF Node]              → Kiểm tra success === true
      ↓                         ↓
8a. [Google Sheets]       8b. [Telegram]
    Cập nhật status           Gửi cảnh báo lỗi
    = "published"
      ↓
9. [Telegram]             → Gửi thông báo: "✅ Đã đăng: {title}"
```

### Code Node — Parse AI Response

```javascript
// Code node trong n8n
const aiResponse = $input.first().json;

// Parse JSON từ AI (AI có thể trả về string)
let parsed;
try {
  parsed = typeof aiResponse.text === 'string' 
    ? JSON.parse(aiResponse.text) 
    : aiResponse.text;
} catch (e) {
  // Thử extract JSON từ markdown code block
  const match = aiResponse.text.match(/```json?\s*([\s\S]*?)\s*```/);
  if (match) {
    parsed = JSON.parse(match[1]);
  } else {
    throw new Error('Không thể parse response từ AI: ' + aiResponse.text.substring(0, 200));
  }
}

// Validate các trường bắt buộc
if (!parsed.title || parsed.title.length < 10) {
  throw new Error('Title không hợp lệ: ' + (parsed.title || 'trống'));
}
if (!parsed.content || parsed.content.length < 300) {
  throw new Error('Content quá ngắn: ' + (parsed.content?.length || 0) + ' ký tự');
}
if (!parsed.content.includes('<h2')) {
  throw new Error('Content thiếu thẻ H2');
}

return [{
  json: {
    title: parsed.title,
    excerpt: parsed.excerpt || '',
    content: parsed.content,
    meta_title: parsed.meta_title || '',
    meta_description: parsed.meta_description || '',
    meta_keywords: parsed.meta_keywords || '',
    category: $input.first().json.category || 'tin-tuc-tong-hop',
    is_published: true,
    is_featured: false,
    is_ai_generated: true,
    ai_model: 'gpt-4o',
    workflow_id: 'daily_news_auto',
    execution_id: $execution.id
  }
}];
```

---

> 📄 **Tài liệu liên quan:**
> - [SEO Content Template](./SEO_CONTENT_TEMPLATE.md) — Form mẫu HTML chuẩn SEO
> - [N8N API Documentation](./N8N_API.md) — Tài liệu API gốc
> - [Database Schema](./DATABASE_SCHEMA.md) — Cấu trúc database
