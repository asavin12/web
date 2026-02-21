# UnstressVN Backup & Restore Guide

## 📋 Tổng quan

Hệ thống backup UnstressVN bao gồm 2 thành phần chính:

1. **Docker Image** (Môi trường + Code): Chứa hệ điều hành, thư viện Python, Django, React code
2. **Database + Media** (Dữ liệu): Chứa dữ liệu người dùng, bài viết, tài khoản, file upload

## 🎯 Cấu trúc Backup

```
backups/
└── unstressvn_backup_YYYYMMDD_HHMMSS/
    ├── unstressvn_image.tar        # Docker image (~500MB-1GB)
    ├── database_backup.sql          # PostgreSQL dump
    ├── media/                       # User uploads (avatars, covers, resources)
    ├── docker-compose.yml           # Docker configuration
    ├── Dockerfile                   # Build instructions
    ├── requirements.txt             # Python dependencies
    ├── .env                         # Environment variables (KEEP SECURE!)
    ├── nginx/                       # Nginx config (if exists)
    └── BACKUP_INFO.txt             # Backup metadata
```

## 🚀 Cách sử dụng

### 1. Backup (Sao lưu)

#### Bước 1: Chuẩn bị
```bash
cd /home/unstress/UnstressVN/UnstressVN
chmod +x scripts/backup.sh
```

#### Bước 2: Chạy backup
```bash
./scripts/backup.sh
```

Script sẽ tự động:
- ✅ Build và export Docker image
- ✅ Dump PostgreSQL database
- ✅ Copy media files (avatars, covers, resources)
- ✅ Copy configuration files
- ✅ Tạo file thông tin backup
- ✅ Nén toàn bộ thành file .tar.gz

#### Kết quả:
```
backups/
├── unstressvn_backup_20251224_120000/      # Folder chưa nén
└── unstressvn_backup_20251224_120000.tar.gz  # File nén (khuyến nghị)
```

### 2. Restore (Khôi phục)

#### Từ folder chưa nén:
```bash
./scripts/restore.sh ./backups/unstressvn_backup_20251224_120000
```

#### Từ file nén:
```bash
./scripts/restore.sh ./backups/unstressvn_backup_20251224_120000.tar.gz
```

Script sẽ tự động:
- ✅ Extract backup (nếu file .tar.gz)
- ✅ Stop các container hiện tại
- ✅ Load Docker image
- ✅ Restore configuration files
- ✅ Start database services
- ✅ Restore database
- ✅ Restore media files
- ✅ Start web application
- ✅ Verify installation

## 📦 Backup thủ công (Manual Backup)

### 1. Backup Docker Image
```bash
# Build image mới nhất
docker-compose build web

# Export image ra file tar
docker save -o unstressvn_image.tar unstressvn_web

# Kích thước: ~500MB-1GB
```

### 2. Backup Database
```bash
# PostgreSQL
docker exec -t unstressvn_db pg_dump -U unstressvn unstressvn > database_backup.sql

# Hoặc với authentication
docker exec -t unstressvn_db pg_dump -U your_user your_database > database_backup.sql
```

### 3. Backup Media Files
```bash
# Copy toàn bộ thư mục media
cp -r ./media ./backup_media/
```

### 4. Backup Configuration
```bash
# Copy các file cấu hình quan trọng
cp docker-compose.yml backup/
cp .env backup/
cp -r nginx/ backup/
```

## 🔄 Restore thủ công (Manual Restore)

### 1. Load Docker Image
```bash
docker load -i unstressvn_image.tar
```

### 2. Copy Configuration Files
```bash
cp backup/docker-compose.yml ./
cp backup/.env ./
cp -r backup/nginx/ ./
```

### 3. Start Services
```bash
docker-compose up -d db redis elasticsearch

# Đợi services khởi động (30 giây)
sleep 30
```

### 4. Restore Database
```bash
# Tạo database mới
docker exec unstressvn_db psql -U unstressvn -c "CREATE DATABASE unstressvn;" postgres

# Restore từ backup
cat database_backup.sql | docker exec -i unstressvn_db psql -U unstressvn unstressvn
```

### 5. Restore Media Files
```bash
cp -r backup_media/ ./media/
```

### 6. Start Web Application
```bash
docker-compose up -d web
```

### 7. Verify
```bash
# Check containers
docker-compose ps

# Test web app
curl http://localhost:8000
```

## 🔒 Bảo mật Backup

### ⚠️ Cảnh báo quan trọng

Backup chứa thông tin nhạy cảm:
- Database credentials (username, password)
- SECRET_KEY của Django
- API keys
- Dữ liệu người dùng (email, password hash)

### 🛡️ Khuyến nghị bảo mật

1. **Mã hóa backup**:
```bash
# Encrypt với GPG
gpg -c unstressvn_backup_20251224_120000.tar.gz

# Decrypt khi cần
gpg unstressvn_backup_20251224_120000.tar.gz.gpg
```

2. **Lưu trữ an toàn**:
- ✅ External hard drive (encrypted)
- ✅ Cloud storage với encryption (AWS S3, Google Drive)
- ✅ NAS với RAID backup
- ❌ KHÔNG để trên server production
- ❌ KHÔNG commit vào Git

3. **Quyền truy cập**:
```bash
# Chỉ owner có quyền đọc
chmod 600 backups/*.tar.gz
chmod 600 .env
```

## 📅 Lịch Backup Khuyến nghị

### Development:
- **Hàng ngày**: Trước khi deploy tính năng mới
- **Trước update lớn**: Backup đầy đủ

### Production:
- **Hàng ngày**: Database backup (automated)
- **Hàng tuần**: Full backup (Docker image + Database + Media)
- **Trước update**: Full backup bắt buộc

### Automation với Cron:
```bash
# Edit crontab
crontab -e

# Backup mỗi ngày lúc 2 giờ sáng
0 2 * * * cd /home/unstress/UnstressVN/UnstressVN && ./scripts/backup.sh >> /var/log/unstressvn_backup.log 2>&1

# Cleanup old backups (giữ 7 ngày gần nhất)
0 3 * * * find /home/unstress/UnstressVN/UnstressVN/backups -name "*.tar.gz" -mtime +7 -delete
```

## 🌍 Chuyển sang máy mới

### Bước 1: Chuẩn bị máy mới
```bash
# Cài đặt Docker và Docker Compose
sudo apt update
sudo apt install docker.io docker-compose

# Clone hoặc tạo thư mục project
mkdir -p /path/to/unstressvn
cd /path/to/unstressvn
```

### Bước 2: Copy backup file
```bash
# Từ máy cũ sang máy mới (qua SSH)
scp unstressvn_backup_20251224_120000.tar.gz user@new-server:/path/to/unstressvn/

# Hoặc dùng rsync
rsync -avz unstressvn_backup_20251224_120000.tar.gz user@new-server:/path/to/unstressvn/
```

### Bước 3: Restore trên máy mới
```bash
# Extract backup
tar -xzf unstressvn_backup_20251224_120000.tar.gz
cd unstressvn_backup_20251224_120000

# Copy restore script từ backup
chmod +x restore.sh
./restore.sh ./
```

### Bước 4: Cập nhật DNS/Domain
```bash
# Update .env với domain mới
nano .env

# Sửa ALLOWED_HOSTS
ALLOWED_HOSTS=new-domain.com,www.new-domain.com

# Restart
docker-compose restart web
```

## 🐛 Troubleshooting

### Lỗi: "Database container not running"
```bash
# Check status
docker-compose ps

# Start database
docker-compose up -d db

# Check logs
docker-compose logs db
```

### Lỗi: "Permission denied"
```bash
# Cấp quyền execute
chmod +x scripts/backup.sh
chmod +x scripts/restore.sh

# Fix ownership
sudo chown -R $USER:$USER ./backups
```

### Lỗi: "Disk space full"
```bash
# Check disk space
df -h

# Cleanup old Docker images
docker system prune -a

# Remove old backups
rm -rf backups/unstressvn_backup_old*
```

### Lỗi: "Database restore failed"
```bash
# Check database logs
docker-compose logs db

# Try manual restore
docker exec -i unstressvn_db psql -U unstressvn unstressvn < database_backup.sql

# Check for encoding issues
file database_backup.sql
```

## 📊 Kích thước Backup ước tính

| Component | Size |
|-----------|------|
| Docker Image | 500MB - 1GB |
| Database (PostgreSQL) | 10MB - 500MB (depends on data) |
| Media Files | 100MB - 5GB (depends on uploads) |
| Configuration | < 1MB |
| **Total (compressed)** | **~200MB - 3GB** |

## 🔗 Resources

- [Docker Save Documentation](https://docs.docker.com/engine/reference/commandline/save/)
- [PostgreSQL Backup Guide](https://www.postgresql.org/docs/current/backup.html)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

## 📞 Support

Nếu gặp vấn đề khi backup hoặc restore, vui lòng:
1. Check logs: `docker-compose logs`
2. Verify backup integrity
3. Contact: support@unstressvn.com

---

**Last Updated**: December 24, 2025  
**Version**: 1.0.0
