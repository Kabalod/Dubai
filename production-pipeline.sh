#!/bin/bash

# ========================================
# Production Data Pipeline for Dubai Platform
# Automated scraping and data processing
# ========================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
PAGES_PER_RUN=${1:-100}
CLEAN_DATA=${2:-false}
LOG_FILE="/shared-data/pipeline_$(date +%Y%m%d_%H%M%S).log"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}    Production Data Pipeline           ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >> "$LOG_FILE"
}

# ========================================
# Pre-flight checks
# ========================================

log "🔍 Starting production pipeline checks..."

# Check if services are running
if ! docker ps | grep -q "prod-api"; then
    log_error "Production API service is not running"
    exit 1
fi

if ! docker ps | grep -q "prod-parser"; then
    log_error "Production parser service is not running"
    exit 1
fi

if ! docker ps | grep -q "prod-postgres"; then
    log_error "Production database is not running"
    exit 1
fi

log "✅ All services are running"

# ========================================
# Health checks
# ========================================

log "🏥 Performing health checks..."

check_health() {
    local service=$1
    local url=$2
    
    if curl -f -s "$url" > /dev/null 2>&1; then
        log "✅ $service is healthy"
        return 0
    else
        log_error "$service health check failed"
        return 1
    fi
}

check_health "API Service" "http://localhost:8000/api/health/"
check_health "Parser Service" "http://localhost:8002/health/"

# ========================================
# Step 1: Run PropertyFinder scraper
# ========================================

log "🔍 Step 1: Running PropertyFinder scraper..."
log "Pages to scrape: $PAGES_PER_RUN"

SCRAPE_START_TIME=$(date +%s)

# Calculate page range based on time of day to avoid hitting same pages
HOUR=$(date +%H)
START_PAGE=$(( (HOUR * 10) + 1 ))
END_PAGE=$(( START_PAGE + PAGES_PER_RUN - 1 ))

log "Scraping pages $START_PAGE to $END_PAGE"

# Run scraper with enhanced command
if docker compose -f docker-compose.prod.yml exec -T parser-service \
    python manage.py scrape_properties_enhanced $START_PAGE $END_PAGE \
    --output-dir /shared-data \
    --log-level INFO >> "$LOG_FILE" 2>&1; then
    
    SCRAPE_END_TIME=$(date +%s)
    SCRAPE_DURATION=$((SCRAPE_END_TIME - SCRAPE_START_TIME))
    log "✅ Scraping completed in ${SCRAPE_DURATION}s"
else
    log_error "Scraping failed"
    exit 1
fi

# ========================================
# Step 2: Export data from parser
# ========================================

log "📤 Step 2: Exporting data from parser..."

if docker compose -f docker-compose.prod.yml exec -T parser-service \
    python manage.py export_to_shared \
    --output-dir /shared-data \
    --recent-days 1 >> "$LOG_FILE" 2>&1; then
    
    log "✅ Export completed"
else
    log_error "Export failed"
    exit 1
fi

# ========================================
# Step 3: Import to main database
# ========================================

log "📥 Step 3: Importing to main database..."

IMPORT_FLAGS=""
if [ "$CLEAN_DATA" = "true" ]; then
    IMPORT_FLAGS="--wipe-sale --wipe-rent"
    log "⚠️ Clean import mode enabled"
fi

IMPORT_START_TIME=$(date +%s)

if docker compose -f docker-compose.prod.yml exec -T api-service \
    python manage.py import_properties_enhanced /shared-data/ \
    $IMPORT_FLAGS \
    --batch-size 500 >> "$LOG_FILE" 2>&1; then
    
    IMPORT_END_TIME=$(date +%s)
    IMPORT_DURATION=$((IMPORT_END_TIME - IMPORT_START_TIME))
    log "✅ Import completed in ${IMPORT_DURATION}s"
else
    log_error "Import failed"
    exit 1
fi

# ========================================
# Step 4: Recalculate analytics
# ========================================

log "📊 Step 4: Recalculating analytics..."

if docker compose -f docker-compose.prod.yml exec -T api-service \
    python manage.py recalculate_reports --model building >> "$LOG_FILE" 2>&1; then
    
    log "✅ Analytics recalculated"
else
    log_error "Analytics recalculation failed (non-critical)"
fi

# ========================================
# Step 5: Cleanup old files
# ========================================

log "🧹 Step 5: Cleaning up old files..."

# Remove files older than 7 days
find ./shared-data -name "*.json" -mtime +7 -delete 2>/dev/null || true
find ./shared-data -name "*.log" -mtime +7 -delete 2>/dev/null || true

log "✅ Cleanup completed"

# ========================================
# Step 6: Generate statistics
# ========================================

log "📈 Step 6: Generating statistics..."

# Get current statistics
STATS=$(docker compose -f docker-compose.prod.yml exec -T api-service \
    python manage.py shell -c "
from realty.pfimport.models import PFListSale, PFListRent, Building, Area
from datetime import datetime, timedelta

total_sales = PFListSale.objects.count()
total_rents = PFListRent.objects.count()
total_buildings = Building.objects.count()
total_areas = Area.objects.count()

# Recent data (last 24 hours)
yesterday = datetime.now() - timedelta(days=1)
recent_sales = PFListSale.objects.filter(added_on__gte=yesterday).count()
recent_rents = PFListRent.objects.filter(added_on__gte=yesterday).count()

print(f'Total Sales: {total_sales}')
print(f'Total Rents: {total_rents}')
print(f'Total Buildings: {total_buildings}')
print(f'Total Areas: {total_areas}')
print(f'Recent Sales (24h): {recent_sales}')
print(f'Recent Rents (24h): {recent_rents}')
" 2>/dev/null || echo "Statistics unavailable")

log "📊 Current Statistics:"
echo "$STATS" | while read line; do
    log "   $line"
done

# ========================================
# Success summary
# ========================================

TOTAL_END_TIME=$(date +%s)
TOTAL_DURATION=$((TOTAL_END_TIME - SCRAPE_START_TIME))

log ""
log "🎉 Production pipeline completed successfully!"
log "⏱️ Total duration: ${TOTAL_DURATION}s"
log "📁 Log file: $LOG_FILE"
log "🌐 Application: https://$DOMAIN"
log ""

# ========================================
# Post-pipeline tasks
# ========================================

log "📋 Post-pipeline tasks:"
log "1. Check application: https://$DOMAIN"
log "2. Verify new data in dashboard"
log "3. Monitor logs: docker compose -f docker-compose.prod.yml logs -f"
log "4. Check metrics: http://$DOMAIN:9090 (if monitoring enabled)"

echo -e "${GREEN}✅ Production pipeline completed!${NC}"

# Send completion notification (webhook, email, etc.)
# curl -X POST "https://hooks.slack.com/..." -d '{"text":"Dubai Platform pipeline completed successfully"}'