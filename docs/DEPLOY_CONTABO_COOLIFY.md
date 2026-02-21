# Hướng dẫn Deploy UnstressVN lên Contabo VPS với Coolify

## Mục lục

1. [Tổng quan kiến trúc](#1-tổng-quan-kiến-trúc)
2. [Mua và setup VPS Contabo](#2-mua-và-setup-vps-contabo)
3. [Bảo mật SSH — Đổi port 22 → 1992](#3-bảo-mật-ssh--đổi-port-22--1992)
4. [Cài đặt Coolify (port 9000)](#4-cài-đặt-coolify-port-9000)
5. [Tích hợp Cloudflare](#5-tích-hợp-cloudflare)
6. [Tạo PostgreSQL trên Coolify](#6-tạo-postgresql-trên-coolify)
7. [Push project lên Git](#7-push-project-lên-git)
8. [Deploy ứng dụng trên Coolify](#8-deploy-ứng-dụng-trên-coolify)
9. [Cấu hình Environment Variables](#9-cấu-hình-environment-variables)
10. [Cấu hình Domain & SSL qua Cloudflare](#10-cấu-hình-domain--ssl-qua-cloudflare)
11. [Cấu hình SiteConfiguration](#11-cấu-hình-siteconfiguration)
12. [Persistent Storage (Volumes)](#12-persistent-storage-volumes)
13. [Tạo Superuser](#13-tạo-superuser)
14. [Auto Deploy (CI/CD)](#14-auto-deploy-cicd)
15. [Backup Database](#15-backup-database)
16. [Monitoring & Logs](#16-monitoring--logs)
17. [Troubleshooting](#17-troubleshooting)

---

## 1. Tổng quan kiến trúc

```
Internet
  │
  ▼
Cloudflare (DNS + CDN + WAF + SSL)
  │  ├── Proxy Mode (Orange Cloud) — ẩn IP VPS
  │  ├── DDoS Protection
  │  ├── Cache static assets
  │  └── SSL: Full (Strict)
  │
  ▼
Contabo VPS (Ubuntu 24.04) — SSH port 1992
  │
  └── Coolify (port 9000, self-hosted PaaS)
        │
        ├── Traefik (reverse proxy, port 80/443)
        │     └── unstressvn.com → App container :8000
        │
        ├── App Container (Docker image từ Git)
        │     ├── Gunicorn serve:
        │     │   ├── /api/*          → Django REST API
        │     │   ├── /admin/*        → Django Admin
        │     │   ├── /media-stream/* → Media Streaming
        │     │   ├── /static/*       → Static files
        │     │   ├── /media/*        → User uploads
        │     │   └── /*              → React SPA (index.html)
        │     └── Gunicorn (3 workers) → Django 4.2.17
        │
        └── PostgreSQL 18 (Coolify Database resource)
              └── Database: unstressvn
```

**Cách hoạt động:**
- **Cloudflare** proxy toàn bộ traffic → ẩn IP VPS, chống DDoS, cache CDN, SSL miễn phí
- **PostgreSQL** chạy như **Database resource** trên Coolify
- **App** build từ **Git repository** (Dockerfile), Coolify tự build & deploy
- Push code lên Git → Coolify tự động build & deploy (webhook)
- Toàn bộ chạy trên **root** — Coolify quản lý Docker containers

---

## 2. Mua và setup VPS Contabo

### Chọn gói

Vào [contabo.com](https://contabo.com/en/vps/) → chọn gói **VPS S** (hoặc Cloud VPS 1):
- **4 vCPU / 8 GB RAM / 50 GB SSD** — ~$6.5/tháng
- OS: **Ubuntu 24.04 LTS**
- Location: **Singapore** (gần Việt Nam nhất)

### Sau khi mua

Contabo gửi email chứa:
- **IP address**: ví dụ `45.88.223.89`
- **Root password**

### SSH vào VPS lần đầu

```bash
ssh root@45.88.223.89
# Nhập root password từ email Contabo
```

### Update hệ thống

```bash
apt update && apt upgrade -y
```

---

## 3. Bảo mật SSH — Đổi port 22 → 1992

### Bước 1: Mở file cấu hình SSH

```bash
nano /etc/ssh/sshd_config
```

### Bước 2: Tìm và sửa các dòng sau

```bash
# Tìm dòng "#Port 22" hoặc "Port 22", sửa thành:
Port 1992

# Tìm và đảm bảo các dòng sau đúng:
PermitRootLogin yes
MaxAuthTries 5
```

> **Lưu ý:** Giữ `PermitRootLogin yes` vì chạy trực tiếp trên root.

### Bước 3: Lưu file

Nhấn `Ctrl + O` → `Enter` → `Ctrl + X`

### Bước 4: Cấu hình Firewall (UFW)

```bash
# Cài UFW nếu chưa có
apt install -y ufw

# Cho phép port SSH mới TRƯỚC KHI bật firewall
ufw allow 1992/tcp comment 'SSH'

# Cho phép các port cần thiết
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw allow 9000/tcp comment 'Coolify Dashboard'

# XOÁ rule port 22 cũ (nếu có)
ufw delete allow 22/tcp 2>/dev/null

# Bật firewall
ufw enable

# Kiểm tra rules
ufw status numbered
```

Kết quả mong đợi:
```
Status: active

     To                         Action      From
     --                         ------      ----
[ 1] 1992/tcp                   ALLOW IN    Anywhere        # SSH
[ 2] 80/tcp                     ALLOW IN    Anywhere        # HTTP
[ 3] 443/tcp                    ALLOW IN    Anywhere        # HTTPS
[ 4] 9000/tcp                   ALLOW IN    Anywhere        # Coolify Dashboard
```

### Bước 5: Restart SSH service

```bash
systemctl restart ssh
```

### Bước 6: Test kết nối MỚI (QUAN TRỌNG!)

**KHÔNG đóng terminal hiện tại.** Mở terminal MỚI và test:

```bash
ssh -p 1992 root@45.88.223.89
```

Nếu đăng nhập thành công → OK. Nếu không:
- Quay lại terminal cũ (vẫn đang mở)
- Kiểm tra lại `/etc/ssh/sshd_config`
- Chạy lại `systemctl restart ssh`

### Bước 7: Chặn port 22 (sau khi test thành công)

```bash
# Đảm bảo đã kết nối được qua port 1992 rồi mới chạy
ufw deny 22/tcp
ufw reload
```

### Từ giờ SSH bằng

```bash
ssh -p 1992 root@45.88.223.89
```

---

## 4. Cài đặt Coolify (port 9000)

### Cài đặt

```bash
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
```

Quá trình cài đặt mất ~2-5 phút. Coolify tự cài:
- Docker Engine
- Traefik (reverse proxy)
- Coolify Dashboard

### Đổi port Coolify Dashboard sang 9000

Mặc định Coolify chạy trên port 8000. Đổi sang 9000:

```bash
# Sửa file cấu hình Coolify
nano /data/coolify/source/.env
```

Tìm dòng `APP_PORT` và sửa:
```
APP_PORT=9000
```

Restart Coolify:
```bash
cd /data/coolify/source
docker compose down
docker compose up -d
```

### Truy cập Coolify Dashboard

Mở trình duyệt:
```
http://45.88.223.89:9000
```

- Tạo tài khoản admin (lần đầu)
- Hoàn thành wizard setup ban đầu

---

## 5. Tích hợp Cloudflare

### 5.1 Tạo tài khoản Cloudflare

1. Vào [cloudflare.com](https://cloudflare.com) → đăng ký miễn phí
2. **Add a Site** → nhập `unstressvn.com`
3. Chọn plan **Free**

### 5.2 Chuyển Nameserver

Cloudflare sẽ cung cấp 2 nameserver, ví dụ:
```
ada.ns.cloudflare.com
bob.ns.cloudflare.com
```

Vào **nhà cung cấp domain** (nơi mua `unstressvn.com`) → **DNS Settings** → thay nameserver thành 2 nameserver Cloudflare.

Chờ ~15 phút – 24 giờ để nameserver propagate.

### 5.3 Cấu hình DNS Records

Trong Cloudflare Dashboard → **DNS** → **Records**:

| Type | Name | Content | Proxy | TTL |
|------|------|---------|-------|-----|
| A | `unstressvn.com` | `45.88.223.89` | ☁️ **Proxied** | Auto |
| A | `www` | `45.88.223.89` | ☁️ **Proxied** | Auto |
| A | `coolify` | `45.88.223.89` | ⬜ **DNS only** | Auto |

> **Quan trọng:**
> - Website (`unstressvn.com`, `www`) → **Proxied** (đám mây cam ☁️) để ẩn IP VPS
> - Coolify dashboard (`coolify.unstressvn.com`) → **DNS only** (đám mây xám ⬜) — **BẮT BUỘC!** Coolify chạy trên port 9000 không có SSL, nếu để Proxied sẽ bị lỗi **526 Invalid SSL Certificate**
> - Truy cập Coolify: `http://coolify.unstressvn.com:9000` hoặc `http://45.88.223.89:9000`

### 5.4 Cấu hình SSL/TLS

**Cloudflare Dashboard → SSL/TLS:**

| Setting | Giá trị | Lý do |
|---------|---------|-------|
| **Encryption mode** | **Full (Strict)** | Mã hóa end-to-end, Traefik có cert |
| **Always Use HTTPS** | ✅ ON | Tự redirect HTTP → HTTPS |
| **Minimum TLS Version** | TLS 1.2 | Bảo mật tối thiểu |
| **TLS 1.3** | ✅ ON | Nhanh + an toàn hơn |
| **Automatic HTTPS Rewrites** | ✅ ON | Fix mixed content |

> **Nếu chưa có SSL trên VPS (Traefik chưa cấp cert):** dùng **Full** thay vì **Full (Strict)** tạm thời. Sau khi Coolify cấp cert thành công → chuyển về **Full (Strict)**.

### 5.5 Bảo mật (WAF & Security)

**Cloudflare Dashboard → Security:**

| Setting | Giá trị |
|---------|---------|
| **Security Level** | Medium |
| **Bot Fight Mode** | ✅ ON |
| **Browser Integrity Check** | ✅ ON |
| **Hotlink Protection** | ✅ ON (bảo vệ ảnh) |

**Tạo WAF Rules (tùy chọn):**

1. **Chặn truy cập admin từ nước ngoài:**
   - Cloudflare → **Security** → **WAF** → **Custom Rules** → **Create Rule**
   - Rule name: `Block Admin Non-VN`
   - Expression:
     ```
     (http.request.uri.path contains "/admin" and ip.geoip.country ne "VN")
     ```
   - Action: **Block**

2. **Rate limiting API:**
   - Rule name: `Rate Limit API`
   - Expression:
     ```
     (http.request.uri.path contains "/api/")
     ```
   - Action: **Rate Limit** (100 requests/minute)

### 5.6 Performance & Cache

**Cloudflare Dashboard → Speed:**

| Setting | Giá trị |
|---------|---------|
| **Auto Minify** | ✅ JavaScript, CSS, HTML |
| **Brotli** | ✅ ON |
| **Early Hints** | ✅ ON |
| **HTTP/2** | ✅ ON (mặc định) |

**Cloudflare Dashboard → Caching:**

| Setting | Giá trị |
|---------|---------|
| **Caching Level** | Standard |
| **Browser Cache TTL** | 1 month |

**Cache Rules — Không cache API/Admin:**

1. Cloudflare → **Caching** → **Cache Rules** → **Create Rule**
2. Rule name: `Bypass API and Admin`
3. Expression:
   ```
   (http.request.uri.path contains "/api/") or
   (http.request.uri.path contains "/admin") or
   (http.request.uri.path contains "/media-stream/")
   ```
4. Action: **Bypass Cache**

### 5.7 Page Rules (tùy chọn)

Cloudflare → **Rules** → **Page Rules**:

| URL Pattern | Setting |
|-------------|---------|
| `unstressvn.com/static/*` | Cache Level: **Cache Everything**, Edge Cache TTL: **1 month** |
| `unstressvn.com/media/*` | Cache Level: **Cache Everything**, Edge Cache TTL: **7 days** |
| `unstressvn.com/api/*` | Cache Level: **Bypass** |

### 5.8 Cấu hình Coolify cho Cloudflare

Trong Coolify, khi dùng Cloudflare Proxy, cần cấu hình Traefik tin tưởng Cloudflare IP:

1. Coolify Dashboard → **Settings** → **Configuration**
2. Trong **Proxy Settings**, thêm trusted IPs của Cloudflare

Hoặc trong application settings, đảm bảo:
- **Force HTTPS**: ✅ ON
- Domain format: `https://unstressvn.com` (không phải http)

---

## 6. Tạo PostgreSQL trên Coolify

### Bước 1: Tạo Database Resource

1. Coolify Dashboard → **Projects** → chọn project (hoặc tạo mới)
2. Trong project → **+ New** → **Database** → **PostgreSQL**
3. Chọn version: **18**

### Bước 2: Cấu hình Database

Coolify tự tạo database với thông tin ngẫu nhiên. Sửa lại:

| Field | Giá trị |
|-------|---------|
| **Database Name** | `unstressvn` |
| **Username** | `unstressvn` |
| **Password** | *(để Coolify tự generate hoặc nhập mật khẩu mạnh)* |

### Bước 3: Lưu lại Connection String

Coolify hiển thị **Internal URL** dạng:
```
postgresql://unstressvn:PASSWORD@PROJECT_UUID-db:5432/unstressvn
```

**Ghi nhớ URL này** — dùng làm `DATABASE_URL` cho app ở bước 9.

> **Quan trọng:** Dùng **Internal URL** (không phải Public URL) vì app và DB cùng Docker network.

### Bước 4: Start Database

Bấm **Deploy** / **Start** để khởi động PostgreSQL.

---

## 7. Push project lên Git

### Dùng script commit+push.sh (khuyến nghị)

Trên máy dev (nơi đang phát triển):

```bash
cd /home/unstress

# Chạy script (sẽ tự init git, hỏi remote URL nếu chưa có)
./commit+push.sh "Initial commit - UnstressVN"
```

### Hoặc thủ công

```bash
cd /home/unstress/unstressvn

# Khởi tạo git
git init
git add .
git commit -m "Initial commit - UnstressVN"

# Push lên GitHub
git remote add origin https://github.com/asavin12/web.git
git branch -M main
git push -u origin main
```

### Các file quan trọng phải có trong repo

```
✅ Dockerfile              ← Coolify dùng file này để build image
✅ docker-entrypoint.sh    ← Script khởi động container
✅ .dockerignore            ← Loại bỏ file không cần trong image
✅ requirements.txt        ← Python dependencies
✅ frontend/package.json   ← Frontend dependencies
✅ manage.py               ← Django management
✅ unstressvn_settings/    ← Django settings
```

### Các file KHÔNG push lên Git (đã trong .gitignore)

```
❌ .venv/                  ← Tạo trong Docker
❌ frontend/node_modules/  ← Cài trong Docker
❌ frontend/dist/          ← Build trong Docker
❌ staticfiles/            ← Collect trong Docker
❌ .secret_key             ← Tự tạo trong container
❌ .env                    ← Dùng Coolify env vars
❌ media/*                 ← Persistent volume
❌ backups/*.sql           ← Persistent volume
```

---

## 8. Deploy ứng dụng trên Coolify

### Bước 1: Kết nối Git

1. Coolify Dashboard → **Settings** → **Sources** → **+ New**
2. Chọn **GitHub** (hoặc GitLab)
3. Đăng nhập và authorize Coolify truy cập repo

### Bước 2: Tạo Application

1. Vào **Project** → **+ New** → **Application**
2. Chọn **Git** source → chọn repo `unstressvn`
3. Branch: `main`

### Bước 3: Cấu hình Build

Coolify tự detect `Dockerfile`. Kiểm tra:

| Setting | Giá trị |
|---------|---------|
| **Build Pack** | `Dockerfile` |
| **Dockerfile Location** | `/Dockerfile` |
| **Port** | `8000` |

### Bước 4: Deploy lần đầu

**CHƯA bấm Deploy** — cần cấu hình Environment Variables trước (bước 9).

---

## 9. Cấu hình Environment Variables

Trong Coolify → Application → **Environment Variables**:

### Bắt buộc

| Variable | Giá trị | Mô tả |
|----------|---------|--------|
| `DATABASE_URL` | `postgresql://unstressvn:PASSWORD@HOSTNAME:5432/unstressvn` | Internal URL từ bước 6.3 |
| `DB_HOST` | *(hostname từ DATABASE_URL)* | Hostname PostgreSQL |
| `DB_PORT` | `5432` | Port database |
| `DB_NAME` | `unstressvn` | Tên database |
| `DB_USER` | `unstressvn` | User database |
| `DB_PASSWORD` | *(password từ bước 6)* | Password database |

> **Mẹo:** Coolify hỗ trợ liên kết biến giữa các service. Có thể link trực tiếp đến database resource thay vì nhập thủ công.

### Tùy chọn

| Variable | Giá trị | Mô tả |
|----------|---------|--------|
| `GUNICORN_WORKERS` | `3` | Số worker Gunicorn (mặc định 3) |

### Lưu ý

- Tất cả cấu hình khác (DEBUG, ALLOWED_HOSTS, CORS, SMTP, v.v.) được quản lý qua **SiteConfiguration** trong Django Admin (bước 11) — không cần set env vars.
- `docker-entrypoint.sh` hỗ trợ cả `DATABASE_URL` và `DB_*` riêng lẻ.

### Bấm Deploy

Sau khi set env vars → bấm **Deploy**. Coolify sẽ:
1. Clone repo từ Git
2. Build Docker image (multi-stage: frontend + backend)
3. Start container
4. Chạy migrations tự động
5. Collect static files
6. Start Gunicorn

Theo dõi quá trình build trong tab **Deployments** → xem logs.

---

## 10. Cấu hình Domain & SSL qua Cloudflare

### Bước 1: DNS đã trỏ (bước 5.3)

Đã thực hiện ở bước 5.3. Kiểm tra:
```bash
dig unstressvn.com +short
# Phải trả về IP Cloudflare (vì Proxied), KHÔNG phải IP VPS
```

### Bước 2: Cấu hình domain trong Coolify

1. Coolify → Application → **Settings**
2. **Domains**: nhập `https://unstressvn.com,https://www.unstressvn.com`
3. **SSL**: ✅ bật **Generate SSL** (Let's Encrypt)

> **Với Cloudflare Full (Strict):** Traefik cần có cert hợp lệ. Let's Encrypt qua Coolify hoạt động tốt khi Cloudflare ở mode Full (Strict).

### Bước 3: Redeploy

Bấm **Redeploy** để Traefik cập nhật routing.

### Bước 4: Kiểm tra

```bash
curl -I https://unstressvn.com
# HTTP/2 200
# server: cloudflare
# cf-ray: ...
```

Nếu thấy `server: cloudflare` → Cloudflare proxy đang hoạt động.

---

## 11. Cấu hình SiteConfiguration

Sau khi deploy thành công, truy cập **Django Admin**:

### Bước 1: Truy cập Admin

Mở: `https://unstressvn.com/admin/`

*(Cần tạo superuser trước — xem bước 13)*

### Bước 2: Cập nhật SiteConfiguration

Vào **Core** → **Site Configuration** → sửa:

#### Bắt buộc

| Field | Giá trị |
|-------|---------|
| **Debug mode** | ❌ **Tắt** |
| **Maintenance mode** | ❌ Tắt |
| **Allowed hosts** | `unstressvn.com,www.unstressvn.com` |
| **CSRF trusted origins** | `https://unstressvn.com,https://www.unstressvn.com` |
| **CORS allowed origins** | `https://unstressvn.com,https://www.unstressvn.com` |

#### Email (tùy chọn)

| Field | Giá trị |
|-------|---------|
| SMTP Host | `smtp.gmail.com` |
| SMTP Port | `587` |
| SMTP Username | `unstressvn@gmail.com` |
| SMTP Password | App password từ Google |

#### Khác (tùy chọn)

| Field | Giá trị |
|-------|---------|
| YouTube API Key | Key từ Google Cloud Console |
| Social Media URLs | Facebook, YouTube links |

### Bước 3: Restart container

Sau khi sửa SiteConfiguration → Coolify → Application → **Restart**

*(Cần restart vì `apply_dynamic_settings()` chỉ chạy khi container khởi động)*

---

## 12. Persistent Storage (Volumes)

Container mặc định **mất data** khi redeploy. Cần mount volumes:

### Cấu hình trong Coolify

Coolify → Application → **Storages** → thêm:

| Container Path | Mô tả |
|----------------|--------|
| `/home/unstress/unstressvn/media` | Ảnh upload, covers, avatars |
| `/home/unstress/unstressvn/logs` | Log files |
| `/home/unstress/unstressvn/backups` | Database backups |

> **Quan trọng:** Thêm volumes **trước khi** upload media content. Nếu đã deploy, thêm volumes → **Redeploy**.

---

## 13. Tạo Superuser

### Cách 1: Qua Coolify Terminal

1. Coolify → Application → **Terminal** (Execute Command)
2. Chạy:
```bash
python manage.py createsuperuser
```

### Cách 2: SSH vào VPS

```bash
ssh -p 1992 root@45.88.223.89

# Tìm container ID
docker ps | grep unstressvn

# Exec vào container
docker exec -it CONTAINER_ID bash

# Tạo superuser
python manage.py createsuperuser
```

### Cách 3: Dùng environment variables

Thêm vào Coolify env vars (xoá sau khi tạo xong):

| Variable | Giá trị |
|----------|---------|
| `DJANGO_SUPERUSER_USERNAME` | `admin` |
| `DJANGO_SUPERUSER_EMAIL` | `unstressvn@gmail.com` |
| `DJANGO_SUPERUSER_PASSWORD` | `your-strong-password` |

Rồi chạy trong terminal:
```bash
python manage.py createsuperuser --noinput
```

---

## 14. Auto Deploy (CI/CD)

### Webhook tự động

Coolify tự tạo webhook khi kết nối Git repo:

1. Push code lên `main` branch
2. GitHub gửi webhook → Coolify
3. Coolify tự động pull → build → deploy

**Không cần cấu hình thêm** — tính năng mặc định.

### Quy trình deploy từ máy dev

```bash
# Trên máy dev
cd /home/unstress
./commit+push.sh "fix: sửa lỗi XYZ"

# → GitHub nhận push → gửi webhook → Coolify auto deploy
```

### Quy trình bên trong Coolify

```
Coolify nhận webhook:
  1. Pull latest code từ Git
  2. Build Docker image (multi-stage)
     ├── Stage 1: npm ci + npm run build (frontend)
     └── Stage 2: pip install + collectstatic (backend)
  3. Stop old container
  4. Start new container
     ├── Wait for PostgreSQL
     ├── Run migrations
     ├── Collectstatic
     └── Start Gunicorn
  5. Health check OK → route traffic
```

---

## 15. Backup Database

### Backup thủ công qua SSH

```bash
ssh -p 1992 root@45.88.223.89

# Tìm container PostgreSQL
docker ps | grep postgres

# Backup
docker exec POSTGRES_CONTAINER_ID pg_dump -U unstressvn unstressvn > backup_$(date +%Y%m%d).sql
```

### Backup qua Coolify

Coolify có tính năng **Backup** cho Database resources:
1. Coolify → Database → **Backups**
2. Cấu hình schedule (hàng ngày)
3. Lưu vào S3 hoặc local

### Backup qua app container

```bash
docker exec CONTAINER_ID python manage.py dumpdata --natural-foreign --natural-primary -o /home/unstress/unstressvn/backups/backup.json
```

---

## 16. Monitoring & Logs

### Xem logs

**Qua Coolify:**
- Application → **Logs** — xem Gunicorn/Django logs realtime

**Qua SSH:**
```bash
ssh -p 1992 root@45.88.223.89

# Xem logs container
docker logs -f CONTAINER_ID
docker logs --tail 100 CONTAINER_ID
```

### Cloudflare Analytics

- Cloudflare Dashboard → **Analytics** — xem traffic, requests, threats blocked
- **Security** → **Events** — xem WAF blocks, DDoS attempts

### Monitoring

Coolify hiển thị:
- **CPU / Memory usage** của container
- **Deployment history**
- **Health check status**

---

## 17. Troubleshooting

### Build failed

| Lỗi | Nguyên nhân | Giải pháp |
|-----|-------------|-----------|
| `npm ci` failed | `package-lock.json` thiếu | Chạy `npm install` trên local, commit `package-lock.json` |
| `pip install` failed | Package conflict | Kiểm tra `requirements.txt` |
| `collectstatic` failed | Lỗi import | Thường OK vì có `\|\| true` trong Dockerfile |

### Container không start

| Lỗi | Nguyên nhân | Giải pháp |
|-----|-------------|-----------|
| `PostgreSQL not available` | DB chưa start hoặc sai URL | Kiểm tra DB resource, kiểm tra `DATABASE_URL` |
| `connection refused` | Sai hostname/port | Dùng **Internal URL** từ Coolify |
| `permission denied` | Volume permission | Kiểm tra ownership trong Dockerfile |

### Website lỗi sau deploy

| Lỗi | Nguyên nhân | Giải pháp |
|-----|-------------|-----------|
| 502 Bad Gateway | Container chưa sẵn sàng | Chờ health check, xem logs |
| 521 (Cloudflare) | VPS/container down | Kiểm tra VPS và container status |
| 525 SSL Handshake Failed | SSL mismatch | Cloudflare SSL → **Full** (không Strict) tạm thời |
| CSRF error | CSRF_TRUSTED_ORIGINS sai | Cập nhật SiteConfiguration, restart |
| Static files 404 | Chưa collectstatic | Redeploy |
| Media files lost | Chưa mount volume | Thêm volume → Redeploy |

### Lệnh debug

```bash
ssh -p 1992 root@45.88.223.89

# Xem containers
docker ps -a

# Exec vào app container
docker exec -it CONTAINER_ID bash

# Trong container:
python manage.py check --deploy
python manage.py showmigrations
python manage.py shell
```

---

## Tóm tắt — Deploy từ đầu (Checklist)

```
 1. [ ] Mua VPS Contabo (4 vCPU / 8 GB RAM / Ubuntu 24.04)
 2. [ ] SSH vào VPS, update system
 3. [ ] Đổi SSH port 22 → 1992
 4. [ ] Cài UFW firewall (1992, 80, 443, 9000)
 5. [ ] Cài Coolify, đổi port sang 9000
 6. [ ] Đăng ký Cloudflare, add site unstressvn.com
 7. [ ] Chuyển nameserver sang Cloudflare
 8. [ ] Cấu hình DNS records (A records, Proxied)
 9. [ ] Cấu hình SSL: Full (Strict)
10. [ ] Bật WAF, Bot Fight Mode, Hotlink Protection
11. [ ] Cấu hình cache rules (bypass API/admin)
12. [ ] Tạo PostgreSQL database trên Coolify
13. [ ] Push code lên GitHub: ./commit+push.sh
14. [ ] Kết nối GitHub với Coolify
15. [ ] Tạo Application từ Git repo
16. [ ] Set environment variables (DATABASE_URL, DB_*)
17. [ ] Thêm persistent volumes (media, logs, backups)
18. [ ] Deploy lần đầu
19. [ ] Cấu hình domain + SSL trong Coolify
20. [ ] Tạo superuser (qua Coolify terminal)
21. [ ] Cấu hình SiteConfiguration trong Admin
22. [ ] Restart container
23. [ ] Test: https://unstressvn.com ✅
```

---

## Chi phí hàng tháng

| Dịch vụ | Chi phí |
|---------|---------|
| Contabo VPS S (4vCPU/8GB) | ~$6.5/tháng |
| Domain `.com` | ~$12/năm (~$1/tháng) |
| Cloudflare (Free plan) | Miễn phí |
| SSL (Let's Encrypt + Cloudflare) | Miễn phí |
| Coolify (self-hosted) | Miễn phí |
| **Tổng** | **~$7.5/tháng** |
