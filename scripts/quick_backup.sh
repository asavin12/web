#!/bin/bash

###############################################################################
# Quick Backup Script - Chỉ backup Database và Media
# Dùng cho backup nhanh hàng ngày, không backup Docker image
###############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BACKUP_DIR="./backups/quick"
BACKUP_DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="quick_backup_${BACKUP_DATE}"
DB_CONTAINER="unstressvn_db"
DB_NAME="${POSTGRES_DB:-unstressvn}"
DB_USER="${POSTGRES_USER:-unstressvn}"

mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}"

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   ⚡ QUICK BACKUP (Database + Media)      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Backup Database
echo -e "${YELLOW}💾 Backing up database...${NC}"
if docker ps | grep -q "${DB_CONTAINER}"; then
    docker exec -t "${DB_CONTAINER}" pg_dump -U "${DB_USER}" "${DB_NAME}" > "${BACKUP_DIR}/${BACKUP_NAME}/database.sql"
    DB_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_NAME}/database.sql" | cut -f1)
    echo -e "${GREEN}✓ Database backed up (${DB_SIZE})${NC}"
else
    echo -e "${RED}✗ Database container not running!${NC}"
    exit 1
fi

# Backup Media
echo -e "${YELLOW}🖼️  Backing up media files...${NC}"
if [ -d "./media" ]; then
    cp -r ./media "${BACKUP_DIR}/${BACKUP_NAME}/"
    MEDIA_SIZE=$(du -sh "${BACKUP_DIR}/${BACKUP_NAME}/media" | cut -f1)
    echo -e "${GREEN}✓ Media backed up (${MEDIA_SIZE})${NC}"
else
    echo -e "${YELLOW}No media folder found${NC}"
fi

# Compress
echo -e "${YELLOW}📦 Compressing...${NC}"
cd "${BACKUP_DIR}"
tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}"
rm -rf "${BACKUP_NAME}"
cd - > /dev/null

FINAL_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | cut -f1)

echo ""
echo -e "${GREEN}✅ Quick backup completed!${NC}"
echo -e "📁 Location: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
echo -e "📊 Size: ${FINAL_SIZE}"
echo -e "🕐 Time: $(date)"
