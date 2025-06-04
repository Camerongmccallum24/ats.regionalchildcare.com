#!/bin/bash

# Quick Deployment Script for GRO Early Learning ATS
# This script handles the complete setup from scratch

set -e

echo "🚀 GRO Early Learning ATS - Quick Digital Ocean Deployment"
echo "=========================================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Update system
echo -e "${YELLOW}📦 Updating system packages...${NC}"
apt update && apt upgrade -y

# Install essential tools
echo -e "${YELLOW}🛠️ Installing essential tools...${NC}"
apt install -y curl wget git unzip htop ufw

# Install Docker
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}🐳 Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    usermod -aG docker $USER
    systemctl enable docker
    systemctl start docker
    echo -e "${GREEN}✅ Docker installed${NC}"
else
    echo -e "${GREEN}✅ Docker already installed${NC}"
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}🔧 Installing Docker Compose...${NC}"
    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}✅ Docker Compose installed${NC}"
else
    echo -e "${GREEN}✅ Docker Compose already installed${NC}"
fi

# Configure firewall
echo -e "${YELLOW}🔥 Configuring firewall...${NC}"
ufw --force enable
ufw allow 22    # SSH
ufw allow 80    # HTTP
ufw allow 443   # HTTPS
ufw allow 8001  # Backend API (optional)
echo -e "${GREEN}✅ Firewall configured${NC}"

# Create deployment directory
echo -e "${YELLOW}📁 Setting up deployment directory...${NC}"
cd /home
if [ ! -d "gro-ats" ]; then
    mkdir -p gro-ats
fi
cd gro-ats

# Check if we have deployment files
if [ ! -f "docker-compose.prod.yml" ]; then
    echo -e "${RED}❌ Deployment files not found in current directory${NC}"
    echo -e "${YELLOW}Please upload your deployment files to $(pwd)${NC}"
    echo ""
    echo "Required files:"
    echo "  - docker-compose.prod.yml"
    echo "  - Dockerfile.backend"
    echo "  - Dockerfile.frontend"
    echo "  - .env"
    echo "  - nginx.conf"
    echo "  - backend/ (directory)"
    echo "  - frontend/ (directory)"
    exit 1
fi

# Set up environment
if [ ! -f ".env" ]; then
    if [ -f ".env.production" ]; then
        cp .env.production .env
        echo -e "${GREEN}✅ Environment configured${NC}"
    else
        echo -e "${RED}❌ No .env file found${NC}"
        exit 1
    fi
fi

# Make scripts executable
chmod +x *.sh 2>/dev/null || true

# Deploy the application
echo -e "${YELLOW}🚀 Deploying GRO Early Learning ATS...${NC}"
./deploy.sh

echo ""
echo -e "${GREEN}🎉 Quick deployment completed!${NC}"
echo ""
echo -e "${GREEN}📋 Your ATS is now running at:${NC}"
echo -e "   Frontend: http://$(hostname -I | awk '{print $1}')"
echo -e "   Backend: http://$(hostname -I | awk '{print $1}'):8001/api"
echo ""
echo -e "${YELLOW}⚠️ Next Steps:${NC}"
echo -e "   1. Point your domain ats.regionalchildcare.com to this server IP: $(hostname -I | awk '{print $1}')"
echo -e "   2. Run: ./ssl-setup.sh (after DNS is configured)"
echo -e "   3. Test your application"
echo ""
echo -e "${GREEN}🎯 Management Commands:${NC}"
echo -e "   Health Check: ./health-check.sh"
echo -e "   View Logs: docker-compose -f docker-compose.prod.yml logs"
echo -e "   Backup: ./backup.sh"