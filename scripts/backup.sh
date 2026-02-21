#!/bin/bash

###############################################################################
# UnstressVN Backup Script
# Mục đích: Backup toàn bộ môi trường, code và dữ liệu của UnstressVN
# Tác giả: UnstressVN Team
# Ngày tạo: 2025-12-24
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="./backups"
BACKUP_DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="unstressvn_backup_${BACKUP_DATE}"
IMAGE_NAME="unstressvn-web"
DB_CONTAINER="unstressvn_db"
DB_NAME="${POSTGRES_DB:-unstressvn}"
DB_USER="${POSTGRES_USER:-unstressvn}"

# Tạo thư mục backup
mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         🚀 UNSTRESSVN BACKUP SYSTEM                      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}📅 Backup Date: ${BACKUP_DATE}${NC}"
echo -e "${GREEN}📁 Backup Location: ${BACKUP_DIR}/${BACKUP_NAME}${NC}"
echo ""

###############################################################################
# 1. BACKUP DOCKER IMAGE (Môi trường + Code)
###############################################################################

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}🐳 Step 1: Backing up Docker Image...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check if image exists
if docker images | grep -q "${IMAGE_NAME}"; then
    echo -e "${GREEN}✓ Found image: ${IMAGE_NAME}${NC}"
    
    # Build new image if needed
    echo -e "${BLUE}Building latest image...${NC}"
    DOCKER_BUILDKIT=0 docker compose build --no-cache web
    
    # Export image
    echo -e "${BLUE}Exporting Docker image to tar file...${NC}"
    docker save -o "${BACKUP_DIR}/${BACKUP_NAME}/unstressvn_image.tar" unstressvn-web
    
    IMAGE_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_NAME}/unstressvn_image.tar" | cut -f1)
    echo -e "${GREEN}✓ Docker image backed up successfully (${IMAGE_SIZE})${NC}"
else
    echo -e "${RED}✗ Image ${IMAGE_NAME} not found. Building...${NC}"
    DOCKER_BUILDKIT=0 docker compose build --no-cache web
    docker save -o "${BACKUP_DIR}/${BACKUP_NAME}/unstressvn_image.tar" unstressvn-web
fi

echo ""

###############################################################################
# 2. BACKUP DATABASE (PostgreSQL)
###############################################################################

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}💾 Step 2: Backing up PostgreSQL Database...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check if DB container is running
if docker ps | grep -q "${DB_CONTAINER}"; then
    echo -e "${GREEN}✓ Database container is running${NC}"
    
    # Dump database
    echo -e "${BLUE}Dumping PostgreSQL database...${NC}"
    docker exec -t "${DB_CONTAINER}" pg_dump -U "${DB_USER}" "${DB_NAME}" > "${BACKUP_DIR}/${BACKUP_NAME}/database_backup.sql"
    
    DB_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_NAME}/database_backup.sql" | cut -f1)
    echo -e "${GREEN}✓ Database backed up successfully (${DB_SIZE})${NC}"
else
    echo -e "${RED}✗ Database container is not running!${NC}"
    echo -e "${YELLOW}Starting database container...${NC}"
    docker compose up -d db
    sleep 5
    docker exec -t "${DB_CONTAINER}" pg_dump -U "${DB_USER}" "${DB_NAME}" > "${BACKUP_DIR}/${BACKUP_NAME}/database_backup.sql"
fi

echo ""

###############################################################################
# 3. BACKUP MEDIA FILES (User uploads, avatars, covers)
###############################################################################

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}🖼️  Step 3: Backing up Media Files...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ -d "./media" ]; then
    echo -e "${BLUE}Copying media files...${NC}"
    cp -r ./media "${BACKUP_DIR}/${BACKUP_NAME}/"
    MEDIA_SIZE=$(du -sh "${BACKUP_DIR}/${BACKUP_NAME}/media" | cut -f1)
    echo -e "${GREEN}✓ Media files backed up successfully (${MEDIA_SIZE})${NC}"
else
    echo -e "${YELLOW}⚠ No media folder found, skipping...${NC}"
fi

echo ""

###############################################################################
# 4. BACKUP CONFIGURATION FILES
###############################################################################

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}⚙️  Step 4: Backing up Configuration Files...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Copy configuration files
echo -e "${BLUE}Copying configuration files...${NC}"
cp docker-compose.yml "${BACKUP_DIR}/${BACKUP_NAME}/"
cp Dockerfile "${BACKUP_DIR}/${BACKUP_NAME}/"
cp requirements.txt "${BACKUP_DIR}/${BACKUP_NAME}/"

# Copy .env file (with caution)
if [ -f ".env" ]; then
    cp .env "${BACKUP_DIR}/${BACKUP_NAME}/.env"
    echo -e "${GREEN}✓ .env file included${NC}"
fi

if [ -f ".env.docker" ]; then
    cp .env.docker "${BACKUP_DIR}/${BACKUP_NAME}/.env.docker"
    echo -e "${GREEN}✓ .env.docker file included${NC}"
fi

# Copy nginx config if exists
if [ -d "./nginx" ]; then
    cp -r ./nginx "${BACKUP_DIR}/${BACKUP_NAME}/"
    echo -e "${GREEN}✓ Nginx configuration included${NC}"
fi

echo -e "${GREEN}✓ Configuration files backed up successfully${NC}"
echo ""

###############################################################################
# 5. CREATE BACKUP INFO FILE
###############################################################################

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}📝 Step 5: Creating Backup Information...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

cat > "${BACKUP_DIR}/${BACKUP_NAME}/BACKUP_INFO.txt" << EOF
╔════════════════════════════════════════════════════════════╗
║              UNSTRESSVN BACKUP INFORMATION               ║
╚════════════════════════════════════════════════════════════╝

Backup Date: $(date)
Backup Name: ${BACKUP_NAME}
Hostname: $(hostname)
User: $(whoami)

CONTENTS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ unstressvn_image.tar - Docker Image (Web Application)
✓ database_backup.sql - PostgreSQL Database Dump
✓ media/ - User uploaded files (avatars, covers, resources)
✓ docker-compose.yml - Docker Compose configuration
✓ Dockerfile - Docker build instructions
✓ requirements.txt - Python dependencies
✓ .env - Environment variables (KEEP SECURE!)
✓ nginx/ - Nginx configuration (if exists)

DATABASE INFO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Database: ${DB_NAME}
User: ${DB_USER}
Container: ${DB_CONTAINER}

RESTORE INSTRUCTIONS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Load Docker Image:
   docker load -i unstressvn_image.tar

2. Copy configuration files to project directory

3. Start services:
   docker compose up -d db redis elasticsearch

4. Wait for services to be ready (30 seconds)

5. Restore database:
   cat database_backup.sql | docker exec -i unstressvn_db psql -U \${DB_USER} \${DB_NAME}

6. Copy media files to ./media/

7. Start web application:
   docker compose up -d web

8. Access at: http://localhost:8000

For detailed instructions, see: scripts/restore.sh

⚠️  SECURITY WARNING:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This backup contains sensitive information including:
- Database credentials
- Secret keys
- User data

KEEP THIS BACKUP SECURE AND ENCRYPTED!

EOF

echo -e "${GREEN}✓ Backup information created${NC}"
echo ""

###############################################################################
# 6. COMPRESS BACKUP
###############################################################################

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}📦 Step 6: Compressing Backup...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "${BLUE}Creating compressed archive...${NC}"
cd "${BACKUP_DIR}"
tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}"
cd - > /dev/null

ARCHIVE_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | cut -f1)
echo -e "${GREEN}✓ Backup compressed successfully (${ARCHIVE_SIZE})${NC}"
echo ""

# Calculate total size
TOTAL_SIZE=$(du -sh "${BACKUP_DIR}/${BACKUP_NAME}" | cut -f1)

###############################################################################
# 7. SUMMARY
###############################################################################

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              ✅ BACKUP COMPLETED SUCCESSFULLY              ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📊 BACKUP SUMMARY:${NC}"
echo -e "   • Backup folder: ${BACKUP_DIR}/${BACKUP_NAME}/"
echo -e "   • Compressed archive: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
echo -e "   • Total size (uncompressed): ${TOTAL_SIZE}"
echo -e "   • Archive size: ${ARCHIVE_SIZE}"
echo ""
echo -e "${YELLOW}⚠️  NEXT STEPS:${NC}"
echo -e "   1. Test the backup by running: ./scripts/restore.sh"
echo -e "   2. Copy backup to secure external storage"
echo -e "   3. Encrypt the backup if storing remotely"
echo ""
echo -e "${RED}🔒 SECURITY REMINDER:${NC}"
echo -e "   This backup contains sensitive data. Keep it secure!"
echo ""

# Optional: Remove uncompressed folder to save space
read -p "Remove uncompressed backup folder to save space? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "${BACKUP_DIR}/${BACKUP_NAME}"
    echo -e "${GREEN}✓ Uncompressed folder removed${NC}"
fi

echo ""
echo -e "${BLUE}Backup process completed at $(date)${NC}"
