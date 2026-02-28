# Content Builder Schema — Hướng dẫn sử dụng

> Chuyển đổi dữ liệu JSON cấu trúc → HTML chuẩn SEO cho bài viết News và Knowledge.

## Tổng quan

Content Builder cho phép n8n / AI gửi dữ liệu dạng JSON có cấu trúc thay vì HTML thô.
Hệ thống tự động sinh HTML hoàn chỉnh tuân thủ `SEO_CONTENT_TEMPLATE.md`.

### Endpoints

| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/api/v1/n8n/build-content/` | POST | Chuyển JSON → HTML (preview, không lưu) |
| `/api/v1/n8n/content-schema/` | GET | Lấy danh sách block types + schema |
| `/api/v1/n8n/news/` | POST | Tạo bài News — hỗ trợ `structured_content` |
| `/api/v1/n8n/knowledge/` | POST | Tạo bài Knowledge — hỗ trợ `structured_content` |

### Authentication

Tất cả endpoints yêu cầu header:
```
X-API-Key: <N8N_API_KEY>
```

---

## Cách sử dụng

### Cách 1: Gửi trực tiếp khi tạo bài viết

Gửi field `structured_content` thay vì `content` khi tạo bài:

```json
{
  "title": "5 Mẹo học tiếng Đức hiệu quả",
  "structured_content": {
    "lead": "<p>Học tiếng Đức không khó nếu bạn biết cách.</p>",
    "toc": true,
    "blocks": [
      {"type": "heading", "level": 2, "text": "1. Mở rộng vốn từ vựng"},
      {"type": "paragraph", "text": "Mỗi ngày học 10 từ mới..."}
    ],
    "conclusion": "<p>Hãy thử áp dụng ngay hôm nay!</p>"
  },
  "category": "hoc-tieng-duc",
  "is_published": true,
  "skip_seo_validation": true
}
```

### Cách 2: Preview HTML trước khi tạo bài

```bash
curl -X POST "https://unstressvn.com/api/v1/n8n/build-content/" \
  -H "X-API-Key: <KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "lead": "<p>Giới thiệu...</p>",
    "toc": true,
    "blocks": [...],
    "conclusion": "<p>Tổng kết...</p>"
  }'
```

**Response:**
```json
{
  "success": true,
  "html": "<article>...<\/article>",
  "stats": {
    "word_count": 1250,
    "heading_count": 5,
    "table_count": 2,
    "list_count": 3,
    "has_toc": true,
    "has_conclusion": true,
    "block_summary": {"heading": 5, "paragraph": 8, "table": 2, "list": 3}
  }
}
```

---

## Cấu trúc JSON đầu vào

```json
{
  "lead": "<p>Đoạn mở đầu (lead paragraph).</p>",
  "toc": true,
  "blocks": [
    { "type": "heading", "level": 2, "text": "..." },
    { "type": "paragraph", "text": "..." },
    { "type": "table", "headers": [...], "rows": [...] },
    ...
  ],
  "conclusion": "<p>Đoạn kết luận.</p>"
}
```

| Field | Kiểu | Bắt buộc | Mô tả |
|-------|------|----------|-------|
| `lead` | string (HTML) | Không | Đoạn mở đầu, bọc trong `<p>` |
| `toc` | boolean | Không | `true` = tự động tạo mục lục từ H2 |
| `blocks` | array | **Có** | Mảng các block nội dung |
| `conclusion` | string (HTML) | Không | Đoạn kết luận |

---

## Block Types

### 1. `paragraph` — Đoạn văn

```json
{
  "type": "paragraph",
  "text": "Nội dung đoạn văn. Hỗ trợ <strong>HTML inline</strong>."
}
```

**Output:** `<p>Nội dung đoạn văn...</p>`

---

### 2. `heading` — Tiêu đề

```json
{
  "type": "heading",
  "level": 2,
  "text": "Tiêu đề mục",
  "id": "custom-slug"
}
```

| Field | Kiểu | Mô tả |
|-------|------|-------|
| `level` | int | 2-4 (không dùng H1, auto-cap) |
| `text` | string | Nội dung tiêu đề |
| `id` | string | Tùy chọn — tự sinh từ text nếu bỏ trống |

**Output:** `<h2 id="tieu-de-muc">Tiêu đề mục</h2>`

---

### 3. `table` — Bảng dữ liệu

```json
{
  "type": "table",
  "caption": "Bảng chi phí sinh hoạt",
  "headers": ["Khoản mục", "Chi phí (€)", "Ghi chú"],
  "rows": [
    ["Thuê nhà", "400-800", "Tùy thành phố"],
    ["Ăn uống", "200-300", "Nấu ở nhà"],
    ["Bảo hiểm", "110", "Bắt buộc"]
  ],
  "highlight_first_col": true
}
```

| Field | Kiểu | Mô tả |
|-------|------|-------|
| `caption` | string | Tùy chọn — tiêu đề bảng |
| `headers` | array[string] | Hàng đầu (thead) |
| `rows` | array[array] | Các hàng dữ liệu |
| `highlight_first_col` | boolean | `true` = in đậm cột đầu |

---

### 4. `info_table` — Bảng thông tin (key-value)

Bảng 2 cột cho danh mục thông tin:

```json
{
  "type": "info_table",
  "caption": "Thông tin trường đại học",
  "items": [
    {"label": "Tên trường", "value": "TU München"},
    {"label": "Thành phố", "value": "München"},
    {"label": "Học phí", "value": "Miễn phí"},
    {"label": "Ngôn ngữ", "value": "Tiếng Đức / Tiếng Anh"}
  ]
}
```

| Field | Kiểu | Mô tả |
|-------|------|-------|
| `caption` | string | Tùy chọn |
| `items` | array[{label, value}] | Danh sách cặp key-value |

**Output:** Bảng 2 cột "Thông tin" + "Chi tiết"

---

### 5. `comparison_table` — Bảng so sánh

Đặc biệt hữu ích cho so sánh sản phẩm/dịch vụ:

```json
{
  "type": "comparison_table",
  "caption": "So sánh chương trình học bổng",
  "subjects": ["DAAD", "Erasmus+", "Konrad Adenauer"],
  "criteria": [
    {"name": "Học phí", "values": ["Toàn phần", "Một phần", "Toàn phần"]},
    {"name": "Sinh hoạt phí", "values": [true, false, true]},
    {"name": "Bảo hiểm", "values": [true, true, false]},
    {"name": "Thời gian", "values": ["2 năm", "1 năm", "3 năm"]}
  ]
}
```

| Field | Kiểu | Mô tả |
|-------|------|-------|
| `caption` | string | Tùy chọn |
| `subjects` | array[string] | Header row — các đối tượng so sánh |
| `criteria` | array | Các tiêu chí so sánh |
| `criteria[].name` | string | Tên tiêu chí |
| `criteria[].values` | array | Giá trị cho mỗi subject. `true` → ✅, `false` → ❌ |

---

### 6. `list` — Danh sách

```json
{
  "type": "list",
  "ordered": false,
  "items": [
    "Mục 1",
    "Mục 2 có <strong>HTML</strong>",
    "Mục 3"
  ]
}
```

| Field | Kiểu | Mô tả |
|-------|------|-------|
| `ordered` | boolean | `true` = `<ol>`, `false` = `<ul>` (default) |
| `items` | array[string] | Các mục, hỗ trợ HTML inline |

---

### 7. `blockquote` — Trích dẫn

```json
{
  "type": "blockquote",
  "text": "Học, học nữa, học mãi.",
  "cite": "Lenin"
}
```

| Field | Kiểu | Mô tả |
|-------|------|-------|
| `text` | string | Nội dung trích dẫn |
| `cite` | string | Tùy chọn — nguồn trích dẫn |

---

### 8. `image` — Hình ảnh

```json
{
  "type": "image",
  "src": "https://example.com/photo.jpg",
  "alt": "Mô tả hình ảnh cho SEO",
  "caption": "Hình 1: Campus TU München"
}
```

| Field | Kiểu | Mô tả |
|-------|------|-------|
| `src` | string | URL hình ảnh |
| `alt` | string | Alt text (quan trọng cho SEO) |
| `caption` | string | Tùy chọn — chú thích dưới ảnh |

**Output:** `<figure>` với `<img>` và `<figcaption>`

---

### 9. `video` — Video nhúng

```json
{
  "type": "video",
  "src": "https://www.youtube.com/embed/VIDEO_ID",
  "title": "Hướng dẫn quá trình xin visa",
  "caption": "Video: Quy trình xin visa Đức 2025"
}
```

| Field | Kiểu | Mô tả |
|-------|------|-------|
| `src` | string | Embed URL (YouTube, Vimeo...) |
| `title` | string | Tiêu đề |
| `caption` | string | Tùy chọn — chú thích |

---

### 10. `code` — Đoạn code

```json
{
  "type": "code",
  "language": "python",
  "code": "print('Xin chào!')"
}
```

---

### 11. `faq` — FAQ Schema (SEO structured data)

```json
{
  "type": "faq",
  "items": [
    {
      "question": "Học phí tại Đức là bao nhiêu?",
      "answer": "Hầu hết trường công lập ở Đức <strong>không thu học phí</strong>."
    },
    {
      "question": "Cần trình độ tiếng Đức nào?",
      "answer": "Tối thiểu B1-B2 cho chương trình tiếng Đức."
    }
  ]
}
```

**Output:** 
- HTML accordion-style với `<details>` / `<summary>`
- Tự động thêm `<script type="application/ld+json">` cho Google FAQ Schema

---

### 12. `divider` — Đường kẻ phân cách

```json
{ "type": "divider" }
```

**Output:** `<hr>`

---

### 13. `callout` — Hộp nổi bật (tip/warning/info)

```json
{
  "type": "callout",
  "style": "tip",
  "title": "Mẹo hay",
  "text": "Luôn đăng ký sớm 6 tháng trước deadline."
}
```

| Field | Kiểu | Mô tả |
|-------|------|-------|
| `style` | string | `tip`, `warning`, `info`, `important` |
| `title` | string | Tùy chọn — tiêu đề hộp |
| `text` | string | Nội dung |

---

### 14. `html` — HTML tùy chỉnh (passthrough)

```json
{
  "type": "html",
  "content": "<div class='custom'>Nội dung HTML tùy ý</div>"
}
```

Dùng khi cần HTML đặc biệt không nằm trong các block type ở trên.

---

## Ví dụ đầy đủ — Bài viết về chi phí du học Đức

```json
{
  "title": "Chi phí du học Đức 2025 - Hướng dẫn chi tiết",
  "structured_content": {
    "lead": "<p>Du học Đức là ước mơ của nhiều sinh viên Việt Nam. Bài viết này tổng hợp chi tiết toàn bộ chi phí bạn cần chuẩn bị.</p>",
    "toc": true,
    "blocks": [
      {
        "type": "heading",
        "level": 2,
        "text": "Tổng quan chi phí du học Đức"
      },
      {
        "type": "paragraph",
        "text": "Chi phí du học Đức bao gồm học phí, sinh hoạt phí, bảo hiểm, và các khoản phụ."
      },
      {
        "type": "info_table",
        "caption": "Tổng quan tài chính",
        "items": [
          {"label": "Học phí trung bình", "value": "0€ (trường công)"},
          {"label": "Sinh hoạt phí/tháng", "value": "850-1.200€"},
          {"label": "Bảo hiểm y tế/tháng", "value": "110€"},
          {"label": "Tổng ngân sách năm", "value": "10.332 - 15.720€"}
        ]
      },
      {
        "type": "heading",
        "level": 2,
        "text": "Chi phí sinh hoạt theo thành phố"
      },
      {
        "type": "paragraph",
        "text": "Chi phí sinh hoạt thay đổi đáng kể giữa các thành phố."
      },
      {
        "type": "table",
        "caption": "So sánh chi phí sinh hoạt các thành phố lớn",
        "headers": ["Thành phố", "Thuê nhà (€)", "Ăn uống (€)", "Tổng/tháng (€)"],
        "rows": [
          ["München", "600-900", "250-350", "1.100-1.500"],
          ["Berlin", "450-700", "200-300", "850-1.200"],
          ["Leipzig", "300-500", "180-250", "650-900"],
          ["Dresden", "280-450", "170-240", "600-850"]
        ],
        "highlight_first_col": true
      },
      {
        "type": "heading",
        "level": 2,
        "text": "So sánh các chương trình học bổng"
      },
      {
        "type": "comparison_table",
        "caption": "Top 3 học bổng phổ biến nhất",
        "subjects": ["DAAD", "Erasmus+", "Konrad Adenauer"],
        "criteria": [
          {"name": "Miễn học phí", "values": [true, true, true]},
          {"name": "Trợ cấp sinh hoạt", "values": [true, false, true]},
          {"name": "Bảo hiểm y tế", "values": [true, true, false]},
          {"name": "Vé máy bay", "values": [true, false, true]},
          {"name": "Thời gian", "values": ["2 năm", "1 năm", "3 năm"]},
          {"name": "Yêu cầu ngôn ngữ", "values": ["B2+", "B1+", "B2+"]}
        ]
      },
      {
        "type": "callout",
        "style": "tip",
        "title": "Mẹo tiết kiệm",
        "text": "Đăng ký Studentenwerk sớm để có suất ký túc xá giá rẻ (200-350€/tháng)."
      },
      {
        "type": "heading",
        "level": 2,
        "text": "Câu hỏi thường gặp"
      },
      {
        "type": "faq",
        "items": [
          {
            "question": "Du học Đức có miễn học phí không?",
            "answer": "Có, hầu hết trường công lập ở Đức không thu học phí. Chỉ có phí semester (150-350€/kỳ)."
          },
          {
            "question": "Cần bao nhiêu tiền trong tài khoản phong tỏa?",
            "answer": "Từ 2024, yêu cầu tối thiểu <strong>11.208€</strong> trong tài khoản phong tỏa (Sperrkonto)."
          },
          {
            "question": "Sinh viên có được đi làm thêm không?",
            "answer": "Được. Sinh viên quốc tế được làm 120 ngày toàn thời gian hoặc 240 ngày bán thời gian mỗi năm."
          }
        ]
      }
    ],
    "conclusion": "<p>Du học Đức hoàn toàn khả thi nếu bạn chuẩn bị tài chính kỹ lưỡng. Hãy bắt đầu từ hôm nay!</p>"
  },
  "category": "du-hoc-duc",
  "is_published": true,
  "meta_title": "Chi phí du học Đức 2025 - Hướng dẫn A-Z",
  "meta_description": "Tổng hợp chi tiết chi phí du học Đức 2025: học phí, sinh hoạt, bảo hiểm, học bổng. Cập nhật mới nhất.",
  "skip_seo_validation": true
}
```

---

## Lấy danh sách block types

```bash
curl -X GET "https://unstressvn.com/api/v1/n8n/content-schema/" \
  -H "X-API-Key: <KEY>"
```

**Response:** Trả về tất cả block types với description + JSON schema mẫu.

---

## Ghi chú quan trọng

1. **H1 không được dùng** — Heading level tự động cap ở 2-4 (H1 dành cho title bài viết)
2. **Mục lục tự động** — Khi `toc: true`, tự sinh `<nav>` từ tất cả block heading level 2
3. **FAQ Schema** — Block `faq` tự thêm JSON-LD structured data cho Google
4. **Comparison table** — `true`/`false` trong values tự chuyển thành ✅/❌
5. **Validation** — SEO validation vẫn chạy trên HTML output. Dùng `skip_seo_validation: true` nếu cần bypass
6. **Fallback** — Nếu gửi cả `content` và `structured_content`, `structured_content` sẽ được ưu tiên

## Xem thêm

- `docs/SEO_CONTENT_TEMPLATE.md` — Template HTML chuẩn SEO
- `docs/N8N_API.md` — Tài liệu API tổng quan
- `api/N8N_API_DOCUMENTATION.md` — Tài liệu chi tiết API
