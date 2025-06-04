#!/bin/bash

# GRO Early Learning ATS - Production Deployment Script
# Usage: ./deploy.sh

set -e

echo "🚀 Starting GRO Early Learning ATS Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    echo -e "${RED}❌ .env.production file not found. Please create it first.${NC}"
    exit 1
fi

# Create necessary directories
echo -e "${YELLOW}📁 Creating necessary directories...${NC}"
mkdir -p logs ssl backups

# Set proper permissions
chmod 755 logs ssl backups

# Pull latest images and build
echo -e "${YELLOW}🔨 Building Docker images...${NC}"
docker-compose -f docker-compose.prod.yml build --no-cache

# Stop existing containers
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker-compose -f docker-compose.prod.yml down

# Start services
echo -e "${YELLOW}🚀 Starting services...${NC}"
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to start...${NC}"
sleep 30

# Check service health
echo -e "${YELLOW}🔍 Checking service health...${NC}"

# Check backend health
if curl -f http://localhost:8001/api/dashboard/stats > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is healthy${NC}"
else
    echo -e "${RED}❌ Backend health check failed${NC}"
    docker-compose -f docker-compose.prod.yml logs backend
    exit 1
fi

# Check frontend health
if curl -f http://localhost/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend is healthy${NC}"
else
    echo -e "${RED}❌ Frontend health check failed${NC}"
    docker-compose -f docker-compose.prod.yml logs frontend
    exit 1
fi

# Check database connection
echo -e "${YELLOW}🔍 Checking database connection...${NC}"
if docker-compose -f docker-compose.prod.yml exec -T backend python -c "
import os
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def test_db():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]
    result = await db.jobs.count_documents({})
    print(f'Database connected. Jobs count: {result}')
    client.close()

asyncio.run(test_db())
" 2>/dev/null; then
    echo -e "${GREEN}✅ Database connection successful${NC}"
else
    echo -e "${RED}❌ Database connection failed${NC}"
    exit 1
fi

# Test webhook connection
echo -e "${YELLOW}🔍 Testing webhook connection...${NC}"
if curl -X POST http://localhost:8001/api/webhooks/test > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Webhook connection test passed${NC}"
else
    echo -e "${YELLOW}⚠️ Webhook connection test failed (may be normal if careers site is not available)${NC}"
fi

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo ""
echo -e "${GREEN}📋 Service URLs:${NC}"
echo -e "   Frontend: http://your-domain.com"
echo -e "   Backend API: http://your-domain.com/api"
echo -e "   Health Check: http://your-domain.com/health"
echo ""
echo -e "${GREEN}📊 Management Commands:${NC}"
echo -e "   View logs: docker-compose -f docker-compose.prod.yml logs"
echo -e "   Stop services: docker-compose -f docker-compose.prod.yml down"
echo -e "   Restart services: docker-compose -f docker-compose.prod.yml restart"
echo ""
echo -e "${YELLOW}⚠️ Next Steps:${NC}"
echo -e "   1. Configure your domain DNS to point to this server"
echo -e "   2. Set up SSL certificates for HTTPS"
echo -e "   3. Configure firewall rules"
echo -e "   4. Set up monitoring and backups"