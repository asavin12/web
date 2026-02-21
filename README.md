# UnstressVN — Nền tảng học ngoại ngữ

## Giới thiệu

UnstressVN là nền tảng học ngoại ngữ (Tiếng Anh / Tiếng Đức) dành cho người Việt, xây dựng theo kiến trúc **Headless CMS** — Django phục vụ Admin + REST API, React SPA xử lý toàn bộ giao diện người dùng.

### Tính năng chính

- 📺 **Video học tập** — Tích hợp YouTube, phân loại theo ngôn ngữ & cấp độ CEFR (A1–C2)
- 📚 **Tài liệu học tập** — Upload/download sách, ebook, audio, PDF, flashcard
- 📰 **Tin tức & Kiến thức** — Hệ thống bài viết theo danh mục, SEO tối ưu (Open Graph, Structured Data)
- 🛠️ **Công cụ học tập** — Flashcard, công cụ nhúng, bài viết hướng dẫn
- 🎬 **Media Streaming** — Phát video/audio với bảo vệ referrer, hỗ trợ phụ đề, MinIO/S3
- 🤖 **N8N Automation API** — Tự động tạo bài viết qua API, hỗ trợ upload ảnh & tạo placeholder
- 🖼️ **WebP Image Pipeline** — Tự động chuyển đổi ảnh sang WebP, tạo responsive srcset, thumbnail, og_image
- 🌐 **Đa ngôn ngữ (i18n)** — Hỗ trợ Tiếng Việt, English, Deutsch
- 🔒 **Cấu hình bảo mật** — Mã hóa Fernet, cấu hình từ database (không cần .env)
- 📊 **Admin Dashboard** — Quản lý PostgreSQL, file manager, backup/restore

---

## Tech Stack

| Layer | Công nghệ | Phiên bản |
|-------|-----------|-----------|
| **Backend** | Django + Django REST Framework | 4.2.17 / 3.16.1 |
| **Database** | PostgreSQL | 16+ (port 5433) |
| **Frontend** | React + TypeScript + Vite | 19.2 / 5.9 / 7.2 |
| **CSS** | Tailwind CSS | 4.1 |
| **Image Processing** | Pillow | 12.0.0 |
| **API Docs** | drf-spectacular (OpenAPI/Swagger) | 0.28.0 |
| **Object Storage** | MinIO/S3 (django-storages + boto3) | 1.14.6 / 1.42.37 |
| **Search** | Elasticsearch (tùy chọn) | — |
| **Cache/Queue** | Redis (tùy chọn) | — |
| **i18n Frontend** | react-i18next | 15.5 |
| **Data Fetching** | @tanstack/react-query | 5.90 |
| **Icons** | lucide-react | 0.525 |
| **SEO** | react-helmet-async | 2.0 |

---

## Yêu cầu hệ thống

- Python 3.12+
- Node.js 18+
- PostgreSQL 16+ (chạy trên port **5433**)

---

## Cài đặt

### 1. Cài đặt PostgreSQL

```bash
sudo apt install postgresql postgresql-contrib
```

### 2. Tạo database (port 5433)

```bash
sudo -u postgres psql -p 5433 -c "CREATE USER unstressvn WITH PASSWORD 'password123' CREATEDB;"
sudo -u postgres psql -p 5433 -c "CREATE DATABASE unstressvn OWNER unstressvn;"
```

### 3. Cài đặt dependencies

```bash
# Backend
cd /home/unstress/unstressvn
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### 4. Chạy migrations & tạo superuser

```bash
cd /home/unstress/unstressvn
source .venv/bin/activate
python manage.py migrate
python manage.py createsuperuser
```

---

## Chạy Development Servers

### Sử dụng scripts (khuyến nghị)

```bash
# Từ thư mục /home/unstress/

# Start cả backend (port 8000) và frontend (port 5173)
./start.sh

# Stop tất cả servers
./stop.sh

# Reset toàn bộ (xoá DB, tạo lại, sample data)
./reset.sh
./reset.sh --no-sample-data   # Không tạo dữ liệu mẫu
./reset.sh --start             # Reset xong tự start
```

### Scripts trong thư mục project

```bash
cd /home/unstress/unstressvn

# Start (kiểm tra PostgreSQL, tự kích hoạt venv)
./dev_start.sh

# Stop
./dev_stop.sh
```

### Chạy thủ công

```bash
# Terminal 1 — Backend (port 8000)
cd /home/unstress/unstressvn
source .venv/bin/activate
python manage.py runserver 0.0.0.0:8000

# Terminal 2 — Frontend (port 5173)
cd /home/unstress/unstressvn/frontend
npm run dev
```

---

## URLs

| URL | Mô tả |
|-----|--------|
| http://localhost:5173 | Frontend SPA (React) |
| http://localhost:8000/admin/ | Django Admin |
| http://localhost:8000/admin-gateway/ | Admin Gateway (yêu cầu secret key) |
| http://localhost:8000/api/v1/ | REST API root |
| http://localhost:8000/api/v1/docs/ | Swagger UI (OpenAPI) |
| http://localhost:8000/api/v1/redoc/ | ReDoc (OpenAPI) |
| http://localhost:8000/sitemap.xml | Sitemap |
| http://localhost:8000/robots.txt | Robots.txt |

---

## Cấu trúc dự án

```
/home/unstress/
├── start.sh                    # Start Django + Vite
├── stop.sh                     # Stop tất cả servers
├── reset.sh                    # Reset toàn bộ hệ thống
└── unstressvn/                 # Project root
    ├── .venv/                  # Python virtual environment
    ├── manage.py               # Django management
    ├── requirements.txt        # Python dependencies
    ├── dev_start.sh            # Dev start script
    ├── dev_stop.sh             # Dev stop script
    ├── pyrightconfig.json      # Python type checking
    │
    ├── unstressvn_settings/    # Django settings
    │   └── settings.py
    │
    ├── accounts/               # Authentication & user profiles
    ├── api/                    # REST API routes & n8n automation
    ├── core/                   # Core models, admin, image utils, signals
    ├── news/                   # Tin tức (articles + categories)
    ├── knowledge/              # Kiến thức (articles + categories)
    ├── tools/                  # Công cụ (tools + flashcards)
    ├── resources/              # Tài liệu học tập
    ├── search/                 # Tìm kiếm (Elasticsearch)
    ├── filemanager/            # Quản lý file (admin)
    ├── mediastream/            # Media streaming (video/audio)
    │
    ├── frontend/               # React SPA
    │   ├── src/
    │   │   ├── components/     # React components
    │   │   ├── pages/          # Page components
    │   │   ├── services/       # API services (axios)
    │   │   ├── types/          # TypeScript types
    │   │   ├── hooks/          # Custom React hooks
    │   │   ├── i18n/           # i18n config + locale files
    │   │   ├── routes/         # React Router config
    │   │   └── utils/          # Utility functions
    │   ├── package.json
    │   └── vite.config.ts
    │
    ├── locale/                 # Django i18n translations
    │   ├── vi/                 # Tiếng Việt
    │   ├── en/                 # English
    │   └── de/                 # Deutsch
    │
    ├── templates/              # Django templates
    │   ├── spa.html            # SPA entry point
    │   ├── 404.html            # Custom 404
    │   ├── admin/              # Admin customizations
    │   └── mediastream/        # Media player templates
    │
    ├── docs/                   # Tài liệu dự án
    │   ├── DATABASE_SCHEMA.md
    │   ├── MEDIA_STREAM.md
    │   ├── N8N_API.md
    │   ├── N8N_AUTO_PUBLISH_GUIDE.md
    │   └── SEO_CONTENT_TEMPLATE.md
    │
    ├── scripts/                # Utility scripts
    │   ├── backup.sh           # Backup database
    │   ├── restore.sh          # Restore database
    │   ├── convert_media_to_webp.py
    │   ├── export_db_schema.py
    │   ├── manage_passwords.py
    │   ├── update_translations.py
    │   └── BACKUP_GUIDE.md
    │
    ├── media/                  # User-uploaded media
    │   ├── avatars/
    │   ├── covers/
    │   ├── logos/
    │   └── resources/
    │
    ├── static/                 # Static files (source)
    ├── staticfiles/            # Collected static files
    └── backups/                # Database backups
```

---

## Django Apps

| App | Mô tả |
|-----|--------|
| **core** | Models cốt lõi: `SiteConfiguration` (singleton), `APIKey`, `Video`, `NavigationLink`. Image utils (WebP pipeline), signals, admin dashboard PostgreSQL |
| **accounts** | Đăng ký/đăng nhập, `UserProfile` (avatar, bio, target language, CEFR level, skill focus). Auto-tạo profile & welcome notification |
| **api** | REST API v1 routes, n8n automation views, serializers, authentication (JWT + API Key) |
| **news** | Tin tức: `Category`, `Article` với cover image (WebP auto), SEO fields, Open Graph, reading time |
| **knowledge** | Kiến thức: `Category`, `KnowledgeArticle` với language/level (CEFR), schema types (Article, HowTo, FAQ, Course) |
| **tools** | Công cụ: `ToolCategory`, `Tool` (internal/external/embed/article), `FlashcardDeck`, `Flashcard` |
| **resources** | Tài liệu: `Category`, `Tag`, `Resource` (book, ebook, audio, PDF, video, flashcard), bookmarks |
| **search** | Tìm kiếm với Elasticsearch (tùy chọn) |
| **filemanager** | File manager trong admin: browse, upload, create folder, delete, rename, disk usage |
| **mediastream** | Media streaming: `StreamMedia`, `MediaSubtitle`, `MediaPlaylist`. Hỗ trợ MinIO/S3, referrer protection |

---

## API Endpoints

### Authentication

| Method | Endpoint | Mô tả |
|--------|----------|--------|
| POST | `/api/v1/auth/login/` | Đăng nhập |
| POST | `/api/v1/auth/logout/` | Đăng xuất |
| POST | `/api/v1/auth/register/` | Đăng ký |
| POST | `/api/v1/auth/password-change/` | Đổi mật khẩu |
| POST | `/api/v1/auth/token/` | Lấy JWT token |
| GET | `/api/v1/me/` | Thông tin user hiện tại |
| GET/PUT | `/api/v1/my-profile/` | Profile user |

### Navigation & General

| Method | Endpoint | Mô tả |
|--------|----------|--------|
| GET | `/api/v1/navigation/` | Navigation links (navbar + footer) |
| GET | `/api/v1/choices/` | Danh sách choices (language, level, etc.) |
| GET | `/api/v1/stats/` | Thống kê tổng hợp |
| POST | `/api/v1/contact/` | Gửi liên hệ |
| GET | `/api/v1/admin-access/` | Kiểm tra quyền admin |

### Videos

| Method | Endpoint | Mô tả |
|--------|----------|--------|
| GET | `/api/v1/videos/` | Danh sách video |
| GET | `/api/v1/videos/<slug>/` | Chi tiết video |

### News (Tin tức)

| Method | Endpoint | Mô tả |
|--------|----------|--------|
| GET | `/api/v1/news/categories/` | Danh sách danh mục tin tức |
| GET | `/api/v1/news/articles/` | Danh sách bài viết |
| GET | `/api/v1/news/articles/<slug>/` | Chi tiết bài viết |

### Knowledge (Kiến thức)

| Method | Endpoint | Mô tả |
|--------|----------|--------|
| GET | `/api/v1/knowledge/categories/` | Danh sách danh mục kiến thức |
| GET | `/api/v1/knowledge/articles/` | Danh sách bài viết |
| GET | `/api/v1/knowledge/articles/<slug>/` | Chi tiết bài viết |

### Tools (Công cụ)

| Method | Endpoint | Mô tả |
|--------|----------|--------|
| GET | `/api/v1/tools/categories/` | Danh sách danh mục công cụ |
| GET | `/api/v1/tools/tools/` | Danh sách công cụ |
| GET | `/api/v1/tools/tools/<slug>/` | Chi tiết công cụ |
| GET | `/api/v1/tools/flashcard-decks/` | Danh sách flashcard decks |

### Resources (Tài liệu)

| Method | Endpoint | Mô tả |
|--------|----------|--------|
| GET | `/api/v1/resources/` | Danh sách tài liệu |
| GET | `/api/v1/resources/<slug>/` | Chi tiết tài liệu |

### Media Streaming

| Method | Endpoint | Mô tả |
|--------|----------|--------|
| GET | `/media-stream/api/media/` | Danh sách media |
| GET | `/media-stream/api/categories/` | Danh sách danh mục media |
| GET | `/media-stream/api/playlists/` | Danh sách playlist |
| GET | `/media-stream/play/<uuid>/` | Phát media |
| GET | `/media-stream/download/<uuid>/` | Download media |
| GET | `/media-stream/info/<uuid>/` | Thông tin media |

### N8N Automation API

Tự động tạo nội dung qua n8n workflow. Xác thực bằng header `X-API-Key`.

| Method | Endpoint | Mô tả |
|--------|----------|--------|
| GET | `/api/v1/n8n/health/` | Kiểm tra API status |
| GET | `/api/v1/n8n/categories/` | Lấy danh mục (theo type: news/knowledge/tools) |
| POST | `/api/v1/n8n/news/` | Tạo bài tin tức |
| POST | `/api/v1/n8n/knowledge/` | Tạo bài kiến thức |
| POST | `/api/v1/n8n/resources/` | Tạo tài liệu |
| POST | `/api/v1/n8n/videos/` | Tạo video |

**Hỗ trợ ảnh trong N8N API:**
- `cover_image_url` — URL ảnh, tự động download & chuyển WebP
- `cover_image` — Upload ảnh trực tiếp (multipart/form-data)
- `auto_placeholder` — Tự động tạo ảnh placeholder nếu không có ảnh (mặc định: `true`)

### Admin Utilities

| Method | Endpoint | Mô tả |
|--------|----------|--------|
| GET | `/admin/core/postgres/` | PostgreSQL Dashboard |
| GET | `/admin/core/postgres/tables/` | Danh sách bảng |
| POST | `/admin/core/postgres/export-schema/` | Export DB schema |
| POST | `/admin/core/postgres/backup/` | Backup database |
| POST | `/admin/core/postgres/restore/` | Restore database |
| GET | `/admin/filemanager/browse/` | File manager |

---

## Frontend Routes

### Trang công khai

| Path | Trang | Mô tả |
|------|-------|--------|
| `/` | HomePage | Trang chủ |
| `/dang-nhap` | LoginPage | Đăng nhập |
| `/dang-ky` | RegisterPage | Đăng ký |
| `/tai-lieu` | ResourceListPage | Danh sách tài liệu |
| `/tai-lieu/:slug` | ResourceDetailPage | Chi tiết tài liệu |
| `/video` | VideoListPage | Danh sách video |
| `/video/:slug` | VideoDetailPage | Chi tiết video |
| `/tin-tuc` | ArticlesPage | Tin tức |
| `/tin-tuc/:categorySlug` | ArticlesPage | Tin tức theo danh mục |
| `/tin-tuc/:categorySlug/:slug` | ArticleDetailPage | Chi tiết tin tức |
| `/kien-thuc` | ArticlesPage | Kiến thức |
| `/kien-thuc/:categorySlug` | ArticlesPage | Kiến thức theo danh mục |
| `/kien-thuc/:categorySlug/:slug` | ArticleDetailPage | Chi tiết kiến thức |
| `/cong-cu` | ArticlesPage | Công cụ |
| `/cong-cu/:categorySlug` | ArticlesPage | Công cụ theo danh mục |
| `/cong-cu/:categorySlug/:slug` | ArticleDetailPage | Chi tiết công cụ |
| `/tim-kiem` | SearchPage | Tìm kiếm |
| `/gioi-thieu` | AboutPage | Giới thiệu |
| `/lien-he` | ContactPage | Liên hệ |
| `/dieu-khoan` | TermsPage | Điều khoản |
| `/chinh-sach-bao-mat` | PrivacyPage | Chính sách bảo mật |

### Trang yêu cầu đăng nhập

| Path | Trang |
|------|-------|
| `/ho-so` | ProfilePage |
| `/ho-so/cap-nhat` | ProfileEditPage |
| `/ho-so/doi-mat-khau` | PasswordChangePage |
| `/cai-dat` | SettingsPage |
| `/thong-bao` | NotificationsPage |

---

## Kiến trúc cấu hình

### Không cần file .env

Toàn bộ cấu hình được quản lý qua **database** thông qua model `SiteConfiguration` (singleton). Dữ liệu nhạy cảm được mã hóa bằng **Fernet** trước khi lưu vào DB.

**Cấu hình bootstrap (hardcoded):**
- `SECRET_KEY` — Tự động tạo, lưu trong file `.secret_key` (không commit git)
- Database — `localhost:5433/unstressvn` (mặc định)

**Cấu hình từ database (`SiteConfiguration`):**
- Debug / Maintenance mode
- Allowed Hosts
- CSRF Trusted Origins
- CORS Origins
- SMTP Email (mã hóa Fernet)
- YouTube API Key (mã hóa Fernet)
- MinIO/S3 Storage (mã hóa Fernet)
- Elasticsearch
- Redis
- Social Media URLs
- Security Headers

Cấu hình dynamic được áp dụng khi server khởi động qua `apply_dynamic_settings()` trong `CoreConfig.ready()`.

---

## WebP Image Pipeline

Hệ thống xử lý ảnh tự động trong `core/image_utils.py`:

### Tính năng
- **Auto WebP conversion** — Tự động chuyển JPG/PNG/GIF/BMP/TIFF sang WebP khi save model
- **Responsive srcset** — Tạo nhiều kích thước (480px, 768px, 1200px, 1920px) cho từng ảnh
- **Auto thumbnail** — Tạo thumbnail 400x267px (WebP, quality 60)
- **Auto og_image** — Tạo ảnh Open Graph cho SEO
- **Placeholder generation** — Tạo ảnh placeholder với gradient + text khi không có ảnh
- **URL download** — Download ảnh từ URL (hỗ trợ n8n automation)
- **Cleanup** — Tự động xóa ảnh responsive cũ khi thay ảnh mới

### WebPImageMixin

Các model `Article` (news), `KnowledgeArticle`, `Tool` đều kế thừa `WebPImageMixin` để tự động:
1. Chuyển `cover_image` sang WebP
2. Tạo `thumbnail`
3. Tạo `og_image`
4. Tạo responsive sizes → lưu vào `cover_image_srcset` (JSONField)

### Frontend ResponsiveImage Component

Component `ResponsiveImage.tsx` render ảnh với `srcset` và `sizes` attributes để trình duyệt tự chọn kích thước phù hợp theo thiết bị.

---

## Middleware

| Middleware | Mô tả |
|-----------|--------|
| `CorsMiddleware` | CORS headers cho React frontend |
| `SecurityMiddleware` | Django security |
| `SessionMiddleware` | Session management |
| `LocaleMiddleware` | Xử lý ngôn ngữ |
| `AdminVietnameseMiddleware` | Force admin panel dùng tiếng Việt |
| `ForceDefaultLanguageMiddleware` | Force ngôn ngữ mặc định |
| `CsrfViewMiddleware` | CSRF protection |
| `AuthenticationMiddleware` | Authentication |
| `AdminAccessMiddleware` | Kiểm soát truy cập admin (admin gateway) |
| `Custom404Middleware` | Custom 404 response cho SPA |

---

## Đa ngôn ngữ (i18n)

### Backend (Django)
- Locale files: `locale/vi/`, `locale/en/`, `locale/de/`
- Ngôn ngữ mặc định: `vi` (Tiếng Việt)
- Quản lý bằng `django.utils.translation`

### Frontend (React)
- Library: `react-i18next`
- Locale files: `frontend/src/i18n/locales/vi.json`, `en.json`, `de.json`
- Ngôn ngữ: Tiếng Việt, English, Deutsch

---

## Scripts & Utilities

### Quản lý servers (`/home/unstress/`)

| Script | Mô tả |
|--------|--------|
| `start.sh` | Kiểm tra PostgreSQL, chạy migrations, start Django (8000) + Vite (5173) |
| `stop.sh` | Kill Django + Vite, giải phóng ports 8000/5173 |
| `reset.sh` | Xoá DB, tạo lại migrations, superuser, sample data |

### Utilities (`scripts/`)

| Script | Mô tả |
|--------|--------|
| `backup.sh` | Backup PostgreSQL database |
| `restore.sh` | Restore database từ backup |
| `convert_media_to_webp.py` | Chuyển tất cả media sang WebP |
| `export_db_schema.py` | Export database schema |
| `manage_passwords.py` | Quản lý mật khẩu |
| `update_translations.py` | Cập nhật i18n translations |
| `generate_logos.py` | Tạo logo |

### Sample data

| Script | Mô tả |
|--------|--------|
| `create_sample_data.py` | Tạo dữ liệu mẫu cơ bản |
| `create_full_sample_data.py` | Tạo đầy đủ dữ liệu mẫu |
| `create_navigation_data.py` | Tạo navigation links |
| `create_tools_sample_data.py` | Tạo dữ liệu công cụ |

---

## Tài liệu bổ sung

| File | Mô tả |
|------|--------|
| `docs/DATABASE_SCHEMA.md` | Schema database chi tiết |
| `docs/MEDIA_STREAM.md` | Hướng dẫn media streaming |
| `docs/N8N_API.md` | Tài liệu N8N API |
| `docs/N8N_AUTO_PUBLISH_GUIDE.md` | Hướng dẫn tự động đăng bài qua n8n |
| `docs/SEO_CONTENT_TEMPLATE.md` | Template SEO cho bài viết |
| `scripts/BACKUP_GUIDE.md` | Hướng dẫn backup/restore |
| `api/N8N_API_DOCUMENTATION.md` | Tài liệu API chi tiết cho n8n |

---

## Liên hệ

- **Website**: https://unstressvn.com
- **Email**: unstressvn@gmail.com
