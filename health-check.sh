#!/bin/bash

# GRO Early Learning ATS - Health Check Script
# Usage: ./health-check.sh

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🔍 GRO Early Learning ATS Health Check${NC}"
echo "======================================"

# Check if services are running
echo -e "${YELLOW}📊 Checking service status...${NC}"

if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    echo -e "${GREEN}✅ Docker services are running${NC}"
else
    echo -e "${RED}❌ Some Docker services are not running${NC}"
    docker-compose -f docker-compose.prod.yml ps
    exit 1
fi

# Check frontend health
echo -e "${YELLOW}🌐 Checking frontend health...${NC}"
if curl -f http://localhost/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend is responding${NC}"
else
    echo -e "${RED}❌ Frontend is not responding${NC}"
fi

# Check backend health
echo -e "${YELLOW}🔧 Checking backend health...${NC}"
if curl -f http://localhost:8001/api/dashboard/stats > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend API is responding${NC}"
else
    echo -e "${RED}❌ Backend API is not responding${NC}"
fi

# Check database connectivity
echo -e "${YELLOW}🗄️ Checking database connectivity...${NC}"
if docker-compose -f docker-compose.prod.yml exec -T backend python -c "
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def test_db():
    try:
        client = AsyncIOMotorClient(os.environ['MONGO_URL'])
        db = client[os.environ['DB_NAME']]
        result = await db.jobs.count_documents({})
        print('Database connected successfully')
        client.close()
        return True
    except Exception as e:
        print(f'Database connection failed: {e}')
        return False

result = asyncio.run(test_db())
exit(0 if result else 1)
" 2>/dev/null; then
    echo -e "${GREEN}✅ Database is connected${NC}"
else
    echo -e "${RED}❌ Database connection failed${NC}"
fi

# Check webhook connectivity
echo -e "${YELLOW}🔗 Checking webhook connectivity...${NC}"
webhook_response=$(curl -s -X POST http://localhost:8001/api/webhooks/test)
if echo "$webhook_response" | grep -q '"success":true'; then
    echo -e "${GREEN}✅ Webhook connection is working${NC}"
else
    echo -e "${YELLOW}⚠️ Webhook connection may have issues${NC}"
fi

# Check disk space
echo -e "${YELLOW}💾 Checking disk space...${NC}"
disk_usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$disk_usage" -lt 80 ]; then
    echo -e "${GREEN}✅ Disk space is sufficient (${disk_usage}% used)${NC}"
elif [ "$disk_usage" -lt 90 ]; then
    echo -e "${YELLOW}⚠️ Disk space is getting high (${disk_usage}% used)${NC}"
else
    echo -e "${RED}❌ Disk space is critically low (${disk_usage}% used)${NC}"
fi

# Check memory usage
echo -e "${YELLOW}🧠 Checking memory usage...${NC}"
memory_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
if [ "$memory_usage" -lt 80 ]; then
    echo -e "${GREEN}✅ Memory usage is normal (${memory_usage}%)${NC}"
elif [ "$memory_usage" -lt 90 ]; then
    echo -e "${YELLOW}⚠️ Memory usage is high (${memory_usage}%)${NC}"
else
    echo -e "${RED}❌ Memory usage is critically high (${memory_usage}%)${NC}"
fi

# Check recent logs for errors
echo -e "${YELLOW}📝 Checking for recent errors...${NC}"
error_count=$(docker-compose -f docker-compose.prod.yml logs --since="1h" 2>&1 | grep -i error | wc -l)
if [ "$error_count" -eq 0 ]; then
    echo -e "${GREEN}✅ No recent errors found${NC}"
elif [ "$error_count" -lt 10 ]; then
    echo -e "${YELLOW}⚠️ ${error_count} errors found in the last hour${NC}"
else
    echo -e "${RED}❌ ${error_count} errors found in the last hour - investigation needed${NC}"
fi

# Summary
echo ""
echo -e "${YELLOW}📋 Health Check Summary${NC}"
echo "======================="

# Get current stats
stats=$(curl -s http://localhost:8001/api/dashboard/stats 2>/dev/null || echo '{"error":"API unavailable"}')
webhook_stats=$(curl -s http://localhost:8001/api/webhooks/stats 2>/dev/null || echo '{"error":"API unavailable"}')

echo "Current time: $(date)"
echo "Uptime: $(uptime -p)"
echo "Jobs in system: $(echo $stats | grep -o '"total_jobs":[0-9]*' | cut -d: -f2 || echo 'N/A')"
echo "Candidates in system: $(echo $stats | grep -o '"total_candidates":[0-9]*' | cut -d: -f2 || echo 'N/A')"
echo "Webhook success rate: $(echo $webhook_stats | grep -o '"success_rate":[0-9.]*' | cut -d: -f2 || echo 'N/A')%"

echo ""
echo -e "${GREEN}🎉 Health check completed!${NC}"