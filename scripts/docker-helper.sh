#!/bin/bash
# Docker helper scripts for UnstressVN
# Sử dụng: ./scripts/docker-helper.sh [command]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_usage() {
    echo "UnstressVN Docker Helper"
    echo "========================="
    echo ""
    echo "Usage: ./scripts/docker-helper.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start       - Start all services (dev mode)"
    echo "  start-prod  - Start all services with Nginx (production)"
    echo "  stop        - Stop all services"
    echo "  restart     - Restart all services"
    echo "  logs        - View logs (all services)"
    echo "  logs-web    - View Django logs only"
    echo "  shell       - Open Django shell"
    echo "  bash        - Open bash in web container"
    echo "  migrate     - Run Django migrations"
    echo "  createsuperuser - Create admin user"
    echo "  collectstatic   - Collect static files"
    echo "  build       - Rebuild Docker images"
    echo "  clean       - Remove all containers and volumes"
    echo "  status      - Show status of all services"
    echo "  es-index    - Rebuild Elasticsearch index"
    echo ""
}

case "$1" in
    start)
        echo -e "${GREEN}🚀 Starting UnstressVN (Development)...${NC}"
        docker compose up -d db redis elasticsearch
        echo "⏳ Waiting for services to be healthy..."
        sleep 10
        docker compose up -d web
        echo -e "${GREEN}✅ All services started!${NC}"
        echo "🌐 Access: http://localhost:8000"
        ;;
    
    start-prod)
        echo -e "${GREEN}🚀 Starting UnstressVN (Production with Nginx)...${NC}"
        docker compose --profile production up -d
        echo -e "${GREEN}✅ All services started!${NC}"
        echo "🌐 Access: http://localhost"
        ;;
    
    stop)
        echo -e "${YELLOW}🛑 Stopping all services...${NC}"
        docker compose --profile production down
        echo -e "${GREEN}✅ All services stopped${NC}"
        ;;
    
    restart)
        echo -e "${YELLOW}🔄 Restarting services...${NC}"
        docker compose restart
        echo -e "${GREEN}✅ Services restarted${NC}"
        ;;
    
    logs)
        docker compose logs -f
        ;;
    
    logs-web)
        docker compose logs -f web
        ;;
    
    shell)
        docker compose exec web python manage.py shell
        ;;
    
    bash)
        docker compose exec web bash
        ;;
    
    migrate)
        echo -e "${GREEN}🔧 Running migrations...${NC}"
        docker compose exec web python manage.py migrate
        echo -e "${GREEN}✅ Migrations completed${NC}"
        ;;
    
    createsuperuser)
        docker compose exec web python manage.py createsuperuser
        ;;
    
    collectstatic)
        echo -e "${GREEN}📦 Collecting static files...${NC}"
        docker compose exec web python manage.py collectstatic --noinput
        echo -e "${GREEN}✅ Static files collected${NC}"
        ;;
    
    build)
        echo -e "${GREEN}🔨 Building Docker images...${NC}"
        docker compose build --no-cache
        echo -e "${GREEN}✅ Build completed${NC}"
        ;;
    
    clean)
        echo -e "${RED}⚠️  This will remove all containers, volumes and data!${NC}"
        read -p "Are you sure? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker compose --profile production down -v --remove-orphans
            echo -e "${GREEN}✅ Cleaned up${NC}"
        fi
        ;;
    
    status)
        echo "📊 Service Status:"
        echo "=================="
        docker compose ps
        ;;
    
    es-index)
        echo -e "${GREEN}🔍 Rebuilding Elasticsearch index...${NC}"
        docker compose exec web python manage.py search_index --rebuild -f
        echo -e "${GREEN}✅ Index rebuilt${NC}"
        ;;
    
    *)
        print_usage
        ;;
esac
