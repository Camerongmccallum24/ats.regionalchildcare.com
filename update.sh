#!/bin/bash

# GRO Early Learning ATS - Update Script
# Usage: ./update.sh

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🔄 Starting GRO Early Learning ATS Update...${NC}"

# Backup before update
echo -e "${YELLOW}📦 Creating backup before update...${NC}"
./backup.sh

# Pull latest code (if using git)
if [ -d ".git" ]; then
    echo -e "${YELLOW}📥 Pulling latest code...${NC}"
    git pull
fi

# Rebuild images
echo -e "${YELLOW}🔨 Rebuilding Docker images...${NC}"
docker-compose -f docker-compose.prod.yml build --no-cache

# Stop services
echo -e "${YELLOW}🛑 Stopping services...${NC}"
docker-compose -f docker-compose.prod.yml down

# Start updated services
echo -e "${YELLOW}🚀 Starting updated services...${NC}"
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to start...${NC}"
sleep 30

# Run health check
echo -e "${YELLOW}🔍 Running health check...${NC}"
./health-check.sh

# Clean up old Docker images
echo -e "${YELLOW}🧹 Cleaning up old Docker images...${NC}"
docker image prune -f

echo -e "${GREEN}✅ Update completed successfully!${NC}"