# UnstressVN Backup Scripts

Hệ thống backup cho UnstressVN bao gồm các script tự động hoá việc sao lưu và khôi phục dữ liệu.

## 📁 Scripts có sẵn

### 1. `backup.sh` - Full Backup (Khuyến nghị)
**Mục đích**: Backup toàn bộ (Docker image + Database + Media + Config)

**Sử dụng**:
```bash
./scripts/backup.sh
```

**Bao gồm**:
- ✅ Docker image (~500MB-1GB)
- ✅ PostgreSQL database
- ✅ Media files (avatars, covers, resources)
- ✅ Configuration files (.env, docker-compose.yml, nginx)
- ✅ Tự động nén thành .tar.gz

**Thời gian**: ~5-15 phút (tùy kích thước)

---

### 2. `quick_backup.sh` - Quick Backup
**Mục đích**: Backup nhanh chỉ Database + Media (không backup Docker image)

**Sử dụng**:
```bash
./scripts/quick_backup.sh
```

**Bao gồm**:
- ✅ PostgreSQL database
- ✅ Media files
- ❌ Docker image (không backup để tiết kiệm thời gian)

**Thời gian**: ~1-3 phút

**Khuyến nghị**: Dùng cho backup hàng ngày

---

### 3. `restore.sh` - Restore
**Mục đích**: Khôi phục từ backup

**Sử dụng**:
```bash
# Từ folder
./scripts/restore.sh ./backups/unstressvn_backup_20251224_120000

# Từ file .tar.gz
./scripts/restore.sh ./backups/unstressvn_backup_20251224_120000.tar.gz
```

**Tự động**:
- ✅ Extract backup
- ✅ Load Docker image
- ✅ Restore database
- ✅ Restore media files
- ✅ Start services
- ✅ Verify installation

---

## 🚀 Quick Start

### Backup lần đầu (Full):
```bash
cd /home/unstress/UnstressVN/UnstressVN
./scripts/backup.sh
```

### Backup hàng ngày (Quick):
```bash
./scripts/quick_backup.sh
```

### Restore khi cần:
```bash
./scripts/restore.sh ./backups/unstressvn_backup_YYYYMMDD_HHMMSS.tar.gz
```

---

## 📂 Cấu trúc thư mục Backup

```
backups/
├── unstressvn_backup_20251224_120000/     # Full backup folder
│   ├── unstressvn_image.tar
│   ├── database_backup.sql
│   ├── media/
│   ├── docker-compose.yml
│   └── ...
├── unstressvn_backup_20251224_120000.tar.gz  # Full backup (compressed)
└── quick/
    └── quick_backup_20251224_150000.tar.gz    # Quick backup
```

---

## ⏰ Tự động hóa với Cron

### Setup backup tự động hàng ngày:

```bash
# Mở crontab editor
crontab -e

# Thêm các dòng sau:

# Full backup mỗi Chủ nhật lúc 2 giờ sáng
0 2 * * 0 cd /home/unstress/UnstressVN/UnstressVN && ./scripts/backup.sh >> /var/log/unstressvn_backup.log 2>&1

# Quick backup mỗi ngày lúc 3 giờ sáng (trừ Chủ nhật)
0 3 * * 1-6 cd /home/unstress/UnstressVN/UnstressVN && ./scripts/quick_backup.sh >> /var/log/unstressvn_quick_backup.log 2>&1

# Cleanup backups cũ (giữ 30 ngày gần nhất)
0 4 * * * find /home/unstress/UnstressVN/UnstressVN/backups -name "*.tar.gz" -mtime +30 -delete
```

### Kiểm tra cron jobs:
```bash
crontab -l
```

### Xem log backup:
```bash
tail -f /var/log/unstressvn_backup.log
tail -f /var/log/unstressvn_quick_backup.log
```

---

## 🔐 Bảo mật

### Mã hóa backup:
```bash
# Encrypt với password
gpg -c backups/unstressvn_backup_20251224_120000.tar.gz

# Decrypt khi cần
gpg backups/unstressvn_backup_20251224_120000.tar.gz.gpg
```

### Set permissions:
```bash
chmod 600 backups/*.tar.gz
chmod 600 .env
```

---

## 📊 So sánh Full vs Quick Backup

| Feature | Full Backup | Quick Backup |
|---------|-------------|--------------|
| Docker Image | ✅ Yes | ❌ No |
| Database | ✅ Yes | ✅ Yes |
| Media Files | ✅ Yes | ✅ Yes |
| Config Files | ✅ Yes | ❌ No |
| Size | ~500MB-3GB | ~50MB-500MB |
| Time | 5-15 min | 1-3 min |
| Use Case | Disaster recovery, Migration | Daily backup |

---

## 🆘 Troubleshooting

### Permission denied:
```bash
chmod +x scripts/*.sh
```

### Container not running:
```bash
docker-compose up -d db
```

### Disk space full:
```bash
# Check space
df -h

# Clean old backups
find ./backups -name "*.tar.gz" -mtime +7 -delete

# Clean Docker
docker system prune -a
```

---

## 📚 Xem thêm

- [BACKUP_GUIDE.md](./BACKUP_GUIDE.md) - Hướng dẫn chi tiết đầy đủ
- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Backup](https://www.postgresql.org/docs/current/backup.html)

---

**Created**: December 24, 2025  
**Last Updated**: December 24, 2025
