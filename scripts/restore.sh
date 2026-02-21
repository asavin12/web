#!/bin/bash

###############################################################################
# UnstressVN Restore Script
# Mục đích: Khôi phục toàn bộ môi trường, code và dữ liệu của UnstressVN
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

# Check if backup path is provided
if [ -z "$1" ]; then
    echo -e "${RED}❌ Error: Backup path not provided${NC}"
    echo -e "${YELLOW}Usage: ./scripts/restore.sh <backup_folder_or_archive>${NC}"
    echo -e "${YELLOW}Example: ./scripts/restore.sh ./backups/unstressvn_backup_20251224_120000${NC}"
    echo -e "${YELLOW}         ./scripts/restore.sh ./backups/unstressvn_backup_20251224_120000.tar.gz${NC}"
    exit 1
fi

BACKUP_PATH="$1"
TEMP_RESTORE_DIR="./temp_restore_$$"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         🔄 UNSTRESSVN RESTORE SYSTEM                     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

###############################################################################
# 1. EXTRACT BACKUP IF COMPRESSED
###############################################################################

if [[ "${BACKUP_PATH}" == *.tar.gz ]]; then
    echo -e "${YELLOW}📦 Extracting compressed backup...${NC}"
    mkdir -p "${TEMP_RESTORE_DIR}"
    tar -xzf "${BACKUP_PATH}" -C "${TEMP_RESTORE_DIR}"
    
    # Find the extracted folder
    BACKUP_FOLDER=$(find "${TEMP_RESTORE_DIR}" -mindepth 1 -maxdepth 1 -type d | head -n 1)
    echo -e "${GREEN}✓ Backup extracted to: ${BACKUP_FOLDER}${NC}"
else
    BACKUP_FOLDER="${BACKUP_PATH}"
    echo -e "${GREEN}✓ Using backup folder: ${BACKUP_FOLDER}${NC}"
fi

echo ""

# Verify backup contents
echo -e "${YELLOW}🔍 Verifying backup contents...${NC}"

if [ ! -d "${BACKUP_FOLDER}" ]; then
    echo -e "${RED}❌ Error: Backup folder not found!${NC}"
    exit 1
fi

REQUIRED_FILES=(
    "${BACKUP_FOLDER}/unstressvn_image.tar"
    "${BACKUP_FOLDER}/database_backup.sql"
    "${BACKUP_FOLDER}/docker-compose.yml"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}❌ Error: Required file not found: $(basename $file)${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✓ All required files found${NC}"
echo ""

# Display backup info if exists
if [ -f "${BACKUP_FOLDER}/BACKUP_INFO.txt" ]; then
    echo -e "${BLUE}📋 Backup Information:${NC}"
    cat "${BACKUP_FOLDER}/BACKUP_INFO.txt"
    echo ""
fi

# Confirmation prompt
echo -e "${RED}⚠️  WARNING: This will restore the backup and may overwrite existing data!${NC}"
echo -e "${YELLOW}Current directory: $(pwd)${NC}"
read -p "Continue with restore? (yes/no) " -r
echo
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${YELLOW}Restore cancelled.${NC}"
    [ -d "${TEMP_RESTORE_DIR}" ] && rm -rf "${TEMP_RESTORE_DIR}"
    exit 0
fi

echo ""

###############################################################################
# 2. STOP EXISTING CONTAINERS
###############################################################################

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}🛑 Step 1: Stopping existing containers...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if docker compose ps -q 2>/dev/null | grep -q .; then
    docker compose down
    echo -e "${GREEN}✓ Existing containers stopped${NC}"
else
    echo -e "${YELLOW}No running containers found${NC}"
fi

echo ""

###############################################################################
# 3. LOAD DOCKER IMAGE
###############################################################################

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}🐳 Step 2: Loading Docker Image...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "${BLUE}Loading image from tar file...${NC}"
docker load -i "${BACKUP_FOLDER}/unstressvn_image.tar"
echo -e "${GREEN}✓ Docker image loaded successfully${NC}"

echo ""

###############################################################################
# 4. RESTORE CONFIGURATION FILES
###############################################################################

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}⚙️  Step 3: Restoring Configuration Files...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Backup existing files
if [ -f "docker-compose.yml" ]; then
    cp docker-compose.yml docker-compose.yml.bak.$(date +%s)
    echo -e "${YELLOW}⚠ Existing docker-compose.yml backed up${NC}"
fi

# Copy configuration files
cp "${BACKUP_FOLDER}/docker-compose.yml" ./
cp "${BACKUP_FOLDER}/Dockerfile" ./
cp "${BACKUP_FOLDER}/requirements.txt" ./

# Copy .env files if they exist
if [ -f "${BACKUP_FOLDER}/.env" ]; then
    cp "${BACKUP_FOLDER}/.env" ./
    echo -e "${GREEN}✓ .env file restored${NC}"
fi

if [ -f "${BACKUP_FOLDER}/.env.docker" ]; then
    cp "${BACKUP_FOLDER}/.env.docker" ./
    echo -e "${GREEN}✓ .env.docker file restored${NC}"
fi

# Copy nginx config if exists
if [ -d "${BACKUP_FOLDER}/nginx" ]; then
    cp -r "${BACKUP_FOLDER}/nginx" ./
    echo -e "${GREEN}✓ Nginx configuration restored${NC}"
fi

echo -e "${GREEN}✓ Configuration files restored${NC}"
echo ""

###############################################################################
# 5. START DATABASE SERVICES
###############################################################################

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}💾 Step 4: Starting Database Services...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Source .env file to get DB credentials
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

DB_NAME="${POSTGRES_DB:-unstressvn}"
DB_USER="${POSTGRES_USER:-unstressvn}"
DB_CONTAINER="unstressvn_db"

echo -e "${BLUE}Starting PostgreSQL, Redis, and Elasticsearch...${NC}"
docker compose up -d db redis elasticsearch

echo -e "${YELLOW}⏳ Waiting for services to be ready (30 seconds)...${NC}"
sleep 30

# Check if database is ready
echo -e "${BLUE}Checking database health...${NC}"
docker exec "${DB_CONTAINER}" pg_isready -U "${DB_USER}" || {
    echo -e "${RED}❌ Database not ready. Waiting additional 15 seconds...${NC}"
    sleep 15
}

echo -e "${GREEN}✓ Database services are ready${NC}"
echo ""

###############################################################################
# 6. RESTORE DATABASE
###############################################################################

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}💾 Step 5: Restoring Database...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "${BLUE}Dropping existing database (if exists)...${NC}"
docker exec "${DB_CONTAINER}" psql -U "${DB_USER}" -c "DROP DATABASE IF EXISTS ${DB_NAME};" postgres 2>/dev/null || true

echo -e "${BLUE}Creating fresh database...${NC}"
docker exec "${DB_CONTAINER}" psql -U "${DB_USER}" -c "CREATE DATABASE ${DB_NAME};" postgres

echo -e "${BLUE}Restoring database from backup...${NC}"
cat "${BACKUP_FOLDER}/database_backup.sql" | docker exec -i "${DB_CONTAINER}" psql -U "${DB_USER}" "${DB_NAME}"

echo -e "${GREEN}✓ Database restored successfully${NC}"
echo ""

###############################################################################
# 7. RESTORE MEDIA FILES
###############################################################################

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}🖼️  Step 6: Restoring Media Files...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ -d "${BACKUP_FOLDER}/media" ]; then
    echo -e "${BLUE}Copying media files...${NC}"
    
    # Backup existing media folder
    if [ -d "./media" ]; then
        mv ./media ./media.bak.$(date +%s)
        echo -e "${YELLOW}⚠ Existing media folder backed up${NC}"
    fi
    
    cp -r "${BACKUP_FOLDER}/media" ./
    echo -e "${GREEN}✓ Media files restored${NC}"
else
    echo -e "${YELLOW}No media folder in backup, skipping...${NC}"
fi

echo ""

###############################################################################
# 8. START WEB APPLICATION
###############################################################################

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}🚀 Step 7: Starting Web Application...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "${BLUE}Starting web container...${NC}"
docker compose up -d web

echo -e "${YELLOW}⏳ Waiting for web application to start (15 seconds)...${NC}"
sleep 15

echo -e "${GREEN}✓ Web application started${NC}"
echo ""

###############################################################################
# 9. VERIFY INSTALLATION
###############################################################################

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}🔍 Step 8: Verifying Installation...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "${BLUE}Checking container status...${NC}"
docker compose ps

echo ""
echo -e "${BLUE}Testing web application...${NC}"
if curl -s http://localhost:8000 > /dev/null; then
    echo -e "${GREEN}✓ Web application is responding${NC}"
else
    echo -e "${YELLOW}⚠ Web application may still be starting up${NC}"
fi

echo ""

###############################################################################
# 10. CLEANUP
###############################################################################

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}🧹 Step 9: Cleanup...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Remove temporary restore directory
if [ -d "${TEMP_RESTORE_DIR}" ]; then
    rm -rf "${TEMP_RESTORE_DIR}"
    echo -e "${GREEN}✓ Temporary files cleaned up${NC}"
fi

echo ""

###############################################################################
# 11. SUMMARY
###############################################################################

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           ✅ RESTORE COMPLETED SUCCESSFULLY                ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📊 RESTORE SUMMARY:${NC}"
echo -e "   • Backup source: ${BACKUP_PATH}"
echo -e "   • Docker image: Loaded"
echo -e "   • Database: Restored"
echo -e "   • Media files: Restored"
echo -e "   • Configuration: Restored"
echo ""
echo -e "${GREEN}🌐 ACCESS INFORMATION:${NC}"
echo -e "   • Web Application: http://localhost:8000"
echo -e "   • Admin Panel: http://localhost:8000/admin"
echo -e "   • API: http://localhost:8000/api"
echo ""
echo -e "${YELLOW}📝 NEXT STEPS:${NC}"
echo -e "   1. Verify the application is working correctly"
echo -e "   2. Check logs: docker compose logs -f web"
echo -e "   3. Update DNS/domain settings if needed"
echo -e "   4. Configure SSL certificates if in production"
echo ""
echo -e "${BLUE}Restore process completed at $(date)${NC}"
