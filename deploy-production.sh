#!/bin/bash

# ========================================
# Dubai Platform MVP - Production Deployment
# ========================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}    Dubai Platform MVP Production      ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if .env.prod exists
if [ ! -f ".env.prod" ]; then
    echo -e "${RED}❌ .env.prod file not found!${NC}"
    echo -e "${YELLOW}Please create .env.prod with production settings.${NC}"
    echo -e "${YELLOW}Copy from .env.prod.example and update with real values.${NC}"
    exit 1
fi

# Check for required environment variables
echo -e "${YELLOW}🔍 Checking environment variables...${NC}"
source .env.prod

REQUIRED_VARS=(
    "POSTGRES_PASSWORD"
    "API_SECRET_KEY" 
    "PARSER_SECRET_KEY"
    "GRAFANA_PASSWORD"
    "DOMAIN"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}❌ Required environment variable $var is not set${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✅ Environment variables validated${NC}"

# Check SSL certificates
echo -e "${YELLOW}🔒 Checking SSL certificates...${NC}"
if [ ! -f "ssl/cert.pem" ] || [ ! -f "ssl/key.pem" ]; then
    echo -e "${YELLOW}⚠️  SSL certificates not found${NC}"
    echo -e "${YELLOW}Creating self-signed certificates for testing...${NC}"
    
    mkdir -p ssl
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout ssl/key.pem \
        -out ssl/cert.pem \
        -subj "/C=AE/ST=Dubai/L=Dubai/O=Dubai Platform/CN=$DOMAIN"
    
    echo -e "${GREEN}✅ Self-signed certificates created${NC}"
    echo -e "${YELLOW}⚠️  Replace with real certificates for production!${NC}"
fi

# Create backup directory
mkdir -p backups

# ========================================
# Pre-deployment checks
# ========================================

echo -e "${YELLOW}🔧 Running pre-deployment checks...${NC}"

# Check Docker
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running${NC}"
    exit 1
fi

# Check Docker Compose
if ! docker compose version > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker Compose not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker environment ready${NC}"

# ========================================
# Backup existing data (if any)
# ========================================

echo -e "${YELLOW}💾 Creating backup...${NC}"
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="backups/backup_${BACKUP_DATE}.sql"

# Create database backup if postgres is running
if docker ps | grep -q postgres; then
    echo -e "${YELLOW}Creating database backup...${NC}"
    docker exec -t postgres pg_dumpall -c -U postgres > "$BACKUP_FILE"
    echo -e "${GREEN}✅ Database backed up to $BACKUP_FILE${NC}"
fi

# ========================================
# Deploy production services
# ========================================

echo -e "${YELLOW}🚀 Deploying production services...${NC}"

# Stop development services
echo -e "${YELLOW}Stopping development services...${NC}"
docker compose -f docker-compose.mvp.yml down 2>/dev/null || true

# Build and deploy production
echo -e "${YELLOW}Building production images...${NC}"
docker compose -f docker-compose.prod.yml build --no-cache

echo -e "${YELLOW}Starting production services...${NC}"
docker compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo -e "${YELLOW}⏳ Waiting for services to be healthy...${NC}"
sleep 30

# ========================================
# Health checks
# ========================================

echo -e "${YELLOW}🏥 Running health checks...${NC}"

check_service() {
    local service_name=$1
    local url=$2
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name: $url${NC}"
            return 0
        fi
        
        echo -e "${YELLOW}⏳ $service_name not ready (attempt $attempt/$max_attempts)${NC}"
        sleep 5
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}❌ $service_name: $url (failed after $max_attempts attempts)${NC}"
    return 1
}

# Check each service
HEALTH_FAILED=0

check_service "API Service" "http://localhost:8000/api/health/" || HEALTH_FAILED=1
check_service "Parser Service" "http://localhost:8002/health/" || HEALTH_FAILED=1
check_service "Frontend" "http://localhost:3000" || HEALTH_FAILED=1
check_service "Nginx" "http://localhost:80/health" || HEALTH_FAILED=1

# ========================================
# Final status
# ========================================

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}    Deployment Status                  ${NC}"
echo -e "${BLUE}========================================${NC}"

if [ $HEALTH_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 Production deployment successful!${NC}"
    echo ""
    echo -e "${GREEN}🌐 Access your application:${NC}"
    echo -e "${GREEN}   Main app: https://$DOMAIN${NC}"
    echo -e "${GREEN}   API: https://$DOMAIN/api/${NC}"
    echo -e "${GREEN}   Admin: https://$DOMAIN/admin/${NC}"
    echo ""
    echo -e "${YELLOW}📊 Monitoring (if enabled):${NC}"
    echo -e "${YELLOW}   Prometheus: http://$DOMAIN:9090${NC}"
    echo -e "${YELLOW}   Grafana: http://$DOMAIN:3003${NC}"
else
    echo -e "${RED}❌ Some services failed health checks${NC}"
    echo -e "${YELLOW}Check logs with: docker compose -f docker-compose.prod.yml logs${NC}"
    exit 1
fi

# ========================================
# Post-deployment tasks
# ========================================

echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo -e "${YELLOW}1. Test the application thoroughly${NC}"
echo -e "${YELLOW}2. Set up SSL certificates (replace self-signed)${NC}"
echo -e "${YELLOW}3. Configure DNS to point to this server${NC}"
echo -e "${YELLOW}4. Set up automated backups${NC}"
echo -e "${YELLOW}5. Configure monitoring alerts${NC}"
echo ""

echo -e "${GREEN}🚀 Production deployment complete!${NC}"