#!/bin/bash

# SSL Certificate Setup Script for GRO Early Learning ATS
# Usage: ./ssl-setup.sh your-domain.com

set -e

DOMAIN=${1:-"ats.regionalchildcare.com"}
EMAIL=${2:-"admin@regionalchildcare.com"}

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🔒 Setting up SSL certificate for ${DOMAIN}...${NC}"

# Check if domain is provided
if [ "$DOMAIN" = "ats.regionalchildcare.com" ] && [ $# -eq 0 ]; then
    echo -e "${YELLOW}Using default domain: ${DOMAIN}${NC}"
    echo "If this is not correct, run: ./ssl-setup.sh your-actual-domain.com"
fi

# Create SSL directory
mkdir -p ssl

# Check if certbot is installed
if ! command -v certbot &> /dev/null; then
    echo -e "${YELLOW}📦 Installing certbot...${NC}"
    
    # For Ubuntu/Debian
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y certbot
    # For CentOS/RHEL
    elif command -v yum &> /dev/null; then
        sudo yum install -y certbot
    else
        echo -e "${RED}❌ Please install certbot manually${NC}"
        exit 1
    fi
fi

# Stop nginx temporarily
echo -e "${YELLOW}🛑 Stopping nginx temporarily...${NC}"
docker-compose -f docker-compose.prod.yml stop frontend

# Generate certificate
echo -e "${YELLOW}🔐 Generating SSL certificate...${NC}"
sudo certbot certonly --standalone \
    --non-interactive \
    --agree-tos \
    --email $EMAIL \
    --domains $DOMAIN

# Copy certificates to ssl directory
echo -e "${YELLOW}📋 Copying certificates...${NC}"
sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ssl/key.pem

# Set proper permissions
sudo chown $(whoami):$(whoami) ssl/cert.pem ssl/key.pem
chmod 644 ssl/cert.pem
chmod 600 ssl/key.pem

# Update nginx configuration for SSL
echo -e "${YELLOW}⚙️ Updating nginx configuration...${NC}"
cat > nginx-ssl.conf << EOF
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    # Logging
    log_format main '\$remote_addr - \$remote_user [\$time_local] "\$request" '
                    '\$status \$body_bytes_sent "\$http_referer" '
                    '"\$http_user_agent" "\$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;
    
    # Basic settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 50M;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone \$binary_remote_addr zone=uploads:10m rate=2r/s;
    
    # Upstream backend
    upstream backend {
        server backend:8001;
    }
    
    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name $DOMAIN;
        return 301 https://\$server_name\$request_uri;
    }
    
    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name $DOMAIN;
        
        # SSL configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        
        # HSTS
        add_header Strict-Transport-Security "max-age=63072000" always;
        
        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;
        add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
        
        # API routes to backend
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://backend;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            
            # Timeouts
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
            
            # CORS headers for API
            add_header Access-Control-Allow-Origin "*" always;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
            add_header Access-Control-Allow-Headers "Authorization, Content-Type, X-Requested-With" always;
            
            if (\$request_method = 'OPTIONS') {
                return 204;
            }
        }
        
        # File upload routes with higher limits
        location /api/candidates/upload-resume {
            limit_req zone=uploads burst=5 nodelay;
            client_max_body_size 10M;
            
            proxy_pass http://backend;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
        
        location /api/documents/upload {
            limit_req zone=uploads burst=5 nodelay;
            client_max_body_size 10M;
            
            proxy_pass http://backend;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
        
        # Frontend static files
        location / {
            root /usr/share/nginx/html;
            index index.html index.htm;
            try_files \$uri \$uri/ /index.html;
            
            # Cache static assets
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
            }
        }
        
        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
EOF

# Replace nginx configuration
mv nginx-ssl.conf nginx.conf

# Set up auto-renewal
echo -e "${YELLOW}🔄 Setting up auto-renewal...${NC}"
(crontab -l 2>/dev/null; echo "0 2 * * * certbot renew --quiet && docker-compose -f $(pwd)/docker-compose.prod.yml restart frontend") | crontab -

# Restart frontend with SSL
echo -e "${YELLOW}🚀 Restarting frontend with SSL...${NC}"
docker-compose -f docker-compose.prod.yml up -d frontend

echo -e "${GREEN}✅ SSL setup completed successfully!${NC}"
echo -e "Your site should now be accessible at: https://$DOMAIN"