#!/bin/bash

# GRO Early Learning ATS - Backup Script
# Usage: ./backup.sh

set -e

# Configuration
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="gro_ats_backup_${DATE}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🔄 Starting backup process...${NC}"

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
echo -e "${YELLOW}📊 Backing up database...${NC}"
docker-compose -f docker-compose.prod.yml exec -T mongodb mongodump \
    --db gro_ats_production \
    --archive=/data/db/backup_${DATE}.archive \
    --gzip

# Copy database backup to host
docker cp gro_ats_mongodb:/data/db/backup_${DATE}.archive $BACKUP_DIR/

# Application logs backup
echo -e "${YELLOW}📝 Backing up application logs...${NC}"
tar -czf $BACKUP_DIR/${BACKUP_FILE}_logs.tar.gz logs/

# Configuration backup
echo -e "${YELLOW}⚙️ Backing up configuration...${NC}"
cp .env.production $BACKUP_DIR/${BACKUP_FILE}_env.bak
cp docker-compose.prod.yml $BACKUP_DIR/${BACKUP_FILE}_compose.yml

# Clean up old backups (keep last 7 days)
echo -e "${YELLOW}🧹 Cleaning up old backups...${NC}"
find $BACKUP_DIR -name "gro_ats_backup_*" -mtime +7 -delete

echo -e "${GREEN}✅ Backup completed successfully!${NC}"
echo -e "Backup files saved in: $BACKUP_DIR"
ls -la $BACKUP_DIR/*${DATE}*