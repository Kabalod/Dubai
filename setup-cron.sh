#!/bin/bash

# ========================================
# Setup automated cron jobs for Dubai Platform
# ========================================

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}    Setting up automated cron jobs     ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${YELLOW}📁 Project directory: $SCRIPT_DIR${NC}"

# Create cron jobs
CRON_FILE="/tmp/dubai_cron"

cat > "$CRON_FILE" << EOF
# Dubai Platform MVP - Automated Tasks
# Generated on $(date)

# ========================================
# Data Pipeline Jobs
# ========================================

# Full scraping and import every 4 hours
0 */4 * * * cd $SCRIPT_DIR && ./production-pipeline.sh 50 false >> ./logs/cron.log 2>&1

# Quick incremental update every hour
0 * * * * cd $SCRIPT_DIR && ./production-pipeline.sh 10 false >> ./logs/cron.log 2>&1

# Weekly full data refresh (Sunday 2 AM)
0 2 * * 0 cd $SCRIPT_DIR && ./production-pipeline.sh 200 true >> ./logs/cron.log 2>&1

# ========================================
# Maintenance Jobs
# ========================================

# Database backup daily at 3 AM
0 3 * * * cd $SCRIPT_DIR && docker exec prod-postgres pg_dumpall -c -U postgres > ./backups/daily_backup_\$(date +\%Y\%m\%d).sql

# Cleanup old backups (keep 7 days)
0 4 * * * find $SCRIPT_DIR/backups -name "*.sql" -mtime +7 -delete

# Cleanup old logs (keep 14 days)
0 5 * * * find $SCRIPT_DIR/logs -name "*.log" -mtime +14 -delete

# Cleanup old shared-data files (keep 3 days)
0 6 * * * find $SCRIPT_DIR/shared-data -name "*.json" -mtime +3 -delete

# ========================================
# Health Check Jobs
# ========================================

# Check services health every 15 minutes
*/15 * * * * cd $SCRIPT_DIR && curl -f http://localhost:80/health > /dev/null 2>&1 || echo "Health check failed at \$(date)" >> ./logs/health.log

# Restart unhealthy services
*/30 * * * * cd $SCRIPT_DIR && docker compose -f docker-compose.prod.yml ps | grep -v "Up" | grep -v "CONTAINER" && docker compose -f docker-compose.prod.yml restart

# ========================================
# Monitoring Jobs
# ========================================

# Generate daily report at 8 AM
0 8 * * * cd $SCRIPT_DIR && docker compose -f docker-compose.prod.yml exec -T api-service python manage.py shell -c "from realty.pfimport.models import *; print(f'Daily Report: Sales={PFListSale.objects.count()}, Rents={PFListRent.objects.count()}')" >> ./logs/daily_report.log

EOF

# Create logs directory
mkdir -p "$SCRIPT_DIR/logs"

# Install cron jobs
echo -e "${YELLOW}📅 Installing cron jobs...${NC}"

if crontab "$CRON_FILE"; then
    echo -e "${GREEN}✅ Cron jobs installed successfully${NC}"
else
    echo -e "${RED}❌ Failed to install cron jobs${NC}"
    exit 1
fi

# Make scripts executable
chmod +x "$SCRIPT_DIR/production-pipeline.sh"
chmod +x "$SCRIPT_DIR/deploy-production.sh"

echo ""
echo -e "${BLUE}📋 Installed cron jobs:${NC}"
echo -e "${YELLOW}• Data pipeline every 4 hours${NC}"
echo -e "${YELLOW}• Quick updates every hour${NC}"
echo -e "${YELLOW}• Weekly full refresh (Sunday 2 AM)${NC}"
echo -e "${YELLOW}• Daily database backup (3 AM)${NC}"
echo -e "${YELLOW}• Automated cleanup and health checks${NC}"
echo ""

echo -e "${BLUE}🔧 Management commands:${NC}"
echo -e "${GREEN}View cron jobs: crontab -l${NC}"
echo -e "${GREEN}Edit cron jobs: crontab -e${NC}"
echo -e "${GREEN}Remove cron jobs: crontab -r${NC}"
echo -e "${GREEN}View logs: tail -f $SCRIPT_DIR/logs/cron.log${NC}"
echo ""

echo -e "${GREEN}✅ Automation setup complete!${NC}"
echo -e "${YELLOW}📊 Check logs in ./logs/ directory${NC}"

# Clean up temp file
rm "$CRON_FILE"