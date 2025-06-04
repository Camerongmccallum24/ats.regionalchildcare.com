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
    echo -e "${RED}❌ Docker is not installed. Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    usermod -aG docker $USER
    echo -e "${GREEN}✅ Docker installed successfully${NC}"
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Installing Docker Compose...${NC}"
    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}✅ Docker Compose installed successfully${NC}"
fi

# Create necessary directories
echo -e "${YELLOW}📁 Creating necessary directories...${NC}"
mkdir -p logs ssl backups
chmod 755 logs ssl backups

# Ensure .env file exists
if [ ! -f ".env" ]; then
    if [ -f ".env.production" ]; then
        echo -e "${YELLOW}📋 Copying .env.production to .env${NC}"
        cp .env.production .env
    else
        echo -e "${RED}❌ No .env file found. Please create .env file first.${NC}"
        exit 1
    fi
fi

# Stop existing containers
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true

# Clean up old images
echo -e "${YELLOW}🧹 Cleaning up old Docker images...${NC}"
docker system prune -f

# Build and start services
echo -e "${YELLOW}🔨 Building and starting services...${NC}"
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to start...${NC}"
sleep 45

# Check service health
echo -e "${YELLOW}🔍 Checking service health...${NC}"

# Check backend health
echo -e "${YELLOW}Testing backend...${NC}"
for i in {1..30}; do
    if curl -f http://localhost:8001/api/dashboard/stats > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend is healthy${NC}"
        break
    elif [ $i -eq 30 ]; then
        echo -e "${RED}❌ Backend health check failed${NC}"
        echo "Backend logs:"
        docker-compose -f docker-compose.prod.yml logs --tail=20 backend
        exit 1
    else
        echo -e "${YELLOW}⏳ Waiting for backend... (attempt $i/30)${NC}"
        sleep 2
    fi
done

# Check frontend health
echo -e "${YELLOW}Testing frontend...${NC}"
for i in {1..30}; do
    if curl -f http://localhost/ > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Frontend is healthy${NC}"
        break
    elif [ $i -eq 30 ]; then
        echo -e "${RED}❌ Frontend health check failed${NC}"
        echo "Frontend logs:"
        docker-compose -f docker-compose.prod.yml logs --tail=20 frontend
        exit 1
    else
        echo -e "${YELLOW}⏳ Waiting for frontend... (attempt $i/30)${NC}"
        sleep 2
    fi
done

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
echo -e "   Frontend: http://$(hostname -I | awk '{print $1}')"
echo -e "   Backend API: http://$(hostname -I | awk '{print $1}'):8001/api"
echo -e "   Health Check: http://$(hostname -I | awk '{print $1}')/health"
echo ""
echo -e "${GREEN}📊 Management Commands:${NC}"
echo -e "   View logs: docker-compose -f docker-compose.prod.yml logs"
echo -e "   Stop services: docker-compose -f docker-compose.prod.yml down"
echo -e "   Restart services: docker-compose -f docker-compose.prod.yml restart"
echo ""
echo -e "${YELLOW}⚠️ Next Steps:${NC}"
echo -e "   1. Configure your domain DNS to point to this server"
echo -e "   2. Run ./ssl-setup.sh to set up HTTPS"
echo -e "   3. Configure firewall rules"
echo -e "   4. Set up monitoring and backups"

# Show final status
echo ""
echo -e "${GREEN}🎯 Current Status:${NC}"
docker-compose -f docker-compose.prod.yml ps