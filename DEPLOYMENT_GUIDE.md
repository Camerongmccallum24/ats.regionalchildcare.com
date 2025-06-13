# 🚀 GRO Early Learning ATS - Digital Ocean Deployment Guide (PostgreSQL)

Complete step-by-step guide to deploy your GRO Early Learning ATS on Digital Ocean using a PostgreSQL database.

## 📋 Prerequisites

- Digital Ocean account
- Domain name (optional but recommended)
- Basic command line knowledge
- An existing PostgreSQL database (version 17 recommended)

## 🖥️ Digital Ocean Droplet Setup

### Step 1: Create a Droplet

1.  **Login to Digital Ocean**
    -   Go to https://www.digitalocean.com/
    -   Click "Create" → "Droplets"

2.  **Configure Droplet**
    -   **Image**: Ubuntu 22.04 LTS
    -   **Plan**:
        -   Basic: $24/month (4GB RAM, 2 vCPUs, 80GB SSD) - Recommended
        -   Or Premium: $48/month (8GB RAM, 2 vCPUs, 160GB SSD) - For high traffic
    -   **Datacenter**: Choose closest to Queensland, Australia (Singapore recommended)
    -   **Authentication**:
        -   Add your SSH key OR
        -   Use password (less secure)
    -   **Hostname**: `gro-ats-production`
    -   **Backups**: Enable (recommended)
    -   **Monitoring**: Enable

3.  **Click "Create Droplet"**

### Step 2: Initial Server Setup

1.  **Connect to your server**


bash ssh root@your_droplet_ip

2.  **Update system packages**


bash apt update && apt upgrade -y

3.  **Create a non-root user**


bash adduser groats usermod -aG sudo groats

4.  **Switch to new user**


bash su - groats

## 🐳 Install Docker and Dependencies

### Step 3: Install Docker


bash

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update sudo apt install -y docker-ce docker-ce-cli containerd.io

sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose sudo chmod +x /usr/local/bin/docker-compose

sudo usermod -aG docker groats newgrp docker

docker --version docker-compose --version

### Step 4: Install Additional Tools


bash

sudo apt install -y git curl wget unzip htop nginx-common certbot postgresql-client # Added postgresql-client for potential debugging

curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - sudo apt install -y nodejs

## 📂 Deploy Application Code

### Step 5: Upload Application Files

**Option A: Using Git (Recommended)**


bash

git clone https://github.com/your-username/gro-early-learning-ats.git cd gro-early-learning-ats

**Option B: Using SCP to upload files**


bash

scp -r /path/to/your/app groats@your_droplet_ip:/home/groats/gro-ats

**Option C: Manual file creation**


bash

mkdir -p /home/groats/gro-ats cd /home/groats/gro-ats

### Step 6: Configure Environment Variables

1.  **Create production environment file**


bash nano .env.production

2.  **Add your production configuration**


env # PostgreSQL Database Configuration DB_USERNAME=your_postgres_username DB_PASSWORD=your_postgres_password DB_HOST=your_postgres_host # e.g., your Digital Ocean Managed Database hostname or droplet IP if local DB_PORT=your_postgres_port # e.g., 5432 DB_DATABASE=your_database_name DB_SSLMODE=require # Or prefer, disable depending on your PostgreSQL setup

# Application Configuration
SECRET_KEY=your_very_long_secure_secret_key_for_jwt_tokens
ATS_DOMAIN=ats.your-domain.com # Your ATS domain

# SendGrid Email Configuration
SENDGRID_API_KEY=SG.your_production_sendgrid_api_key

# Careers Site Integration
CAREERS_SITE_URL=https://childcare-career-hub.lovable.app # The URL of your careers site
CAREERS_WEBHOOK_SECRET=your_secure_webhook_secret_2025

# Application Settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO


3.  **Set proper permissions**


bash chmod 600 .env.production

## 🚀 Deploy the Application

### Step 7: Build and Deploy

1.  **Make deployment script executable**


bash chmod +x deploy.sh backup.sh ssl-setup.sh # Ensure these scripts are updated for PostgreSQL if they interact with the DB

2.  **Run deployment**


bash ./deploy.sh

3.  **Check deployment status**


bash docker-compose -f docker-compose.prod.yml ps docker-compose -f docker-compose.prod.yml logs

## 🔒 Configure SSL/HTTPS (Recommended)

### Step 8: Domain Configuration

1.  **Point your domain to Digital Ocean**
    -   In your domain registrar, update nameservers or A records
    -   Point to your droplet's IP address
    -   Wait for DNS propagation (up to 24 hours)

2.  **Setup SSL certificate**


bash ./ssl-setup.sh your-domain.com admin@yourdomain.com

## 🔥 Configure Firewall

### Step 9: Security Setup


bash

sudo ufw enable

sudo ufw allow 22

sudo ufw allow 80 sudo ufw allow 443

sudo ufw allow 8001 # Backend API (optional, already proxied through nginx)

sudo ufw status

## 📊 Monitoring and Maintenance

### Step 10: Setup Monitoring

1.  **Enable Docker stats monitoring**


bash # Add this to crontab for regular monitoring echo "*/5 * * * * docker stats --no-stream >> /home/groats/gro-ats/logs/docker-stats.log" | crontab -"

2.  **Setup log rotation**


bash sudo nano /etc/logrotate.d/gro-ats

Add:


/home/groats/gro-ats/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}


3.  **Setup automatic backups**


bash # Add to crontab for daily backups at 2 AM # This script needs to be updated to backup your PostgreSQL database echo "0 2 * * * /home/groats/gro-ats/backup.sh" | crontab -"

## 🔧 Application Configuration

### Step 11: Configure Frontend Environment

1.  **Update frontend environment**


bash nano frontend/.env

Update with your production domain:


env REACT_APP_BACKEND_URL=https://your-domain.com

2.  **Rebuild frontend** (if needed)


bash docker-compose -f docker-compose.prod.yml build frontend docker-compose -f docker-compose.prod.yml up -d frontend

## 🧪 Testing Deployment

### Step 12: Verify Everything Works

1.  **Test frontend access**


bash curl -I https://your-domain.com

2.  **Test backend API**


bash curl https://your-domain.com/api/dashboard/stats # Check if dashboard stats are retrieved correctly

3.  **Test webhook connection**


bash curl -X POST https://your-domain.com/api/webhooks/test

4.  **Check all services**


bash docker-compose -f docker-compose.prod.yml ps

## 📈 Performance Optimization

### Step 13: Optimize for Production

1.  **Enable swap** (if needed for smaller droplets)


bash sudo fallocate -l 2G /swapfile sudo chmod 600 /swapfile sudo mkswap /swapfile sudo swapon /swapfile echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

2.  **Configure Docker logging**


bash # Add to docker daemon config sudo nano /etc/docker/daemon.json

Add:


json { "log-driver": "json-file", "log-opts": { "max-size": "10m", "max-file": "3" } }

## 🆘 Troubleshooting

### Common Issues and Solutions

1.  **Port conflicts**


bash sudo netstat -tulpn | grep :80 sudo netstat -tulpn | grep :443

2.  **Docker permission issues**


bash sudo usermod -aG docker $USER newgrp docker

3.  **Database connection issues**


bash # Use psql to test connection to your PostgreSQL database psql "postgresql://your_postgres_username:your_postgres_password@your_postgres_host:your_postgres_port/your_database_name?sslmode=your_sslmode" # Check backend logs for database connection errors docker-compose -f docker-compose.prod.yml logs backend

4.  **SSL certificate issues**


bash sudo certbot certificates sudo certbot renew --dry-run

## 📋 Maintenance Commands

### Regular Maintenance


bash

docker-compose -f docker-compose.prod.yml logs -f

docker-compose -f docker-compose.prod.yml restart

git pull # if using git docker-compose -f docker-compose.prod.yml build docker-compose -f docker-compose.prod.yml up -d

docker system prune -f

htop docker stats

./backup.sh

curl https://your-domain.com/api/webhooks/stats

## 🎯 Final Checklist

-   [ ] Droplet created and configured
-   [ ] Docker and dependencies installed
-   [ ] Application code deployed
-   [ ] Environment variables configured in `.env.production`
-   [ ] PostgreSQL database is running and accessible with provided credentials
-   [ ] PostgreSQL tables created using the provided SQL statements
-   [ ] SSL certificate installed
-   [ ] Firewall configured
-   [ ] Domain DNS configured
-   [ ] Monitoring setup
-   [ ] Backups configured (ensure `backup.sh` is updated for PostgreSQL)
-   [ ] Application tested and working
-   [ ] Webhook integration tested

## 🔗 Useful URLs After Deployment

-   **Frontend**: https://ats.regionalchildchildcare.com (Update with your ATS domain)
-   **Backend API**: https://ats.regionalchildchildcare.com/api (Update with your ATS domain)
-   **Health Check**: https://ats.regionalchildchildcare.com/health (Update with your ATS domain, ensure this endpoint is implemented)
-   **API Documentation**: https://ats.regionalchildchildcare.com/api/docs (if enabled, update with your ATS domain)
-   **Webhook Stats**: https://ats.regionalchildchildcare.com/api/webhooks/stats (Update with your ATS domain)

## 💰 Cost Estimation

**Monthly Costs:**
-   Digital Ocean Droplet: $24-48/month
-   Domain name: $10-15/year
-   Digital Ocean Managed PostgreSQL Database (if used): Starts from $15/month
-   SSL Certificate: Free (Let's Encrypt)
-   **Total: ~$25+ /month** (Depends heavily on database costs)

## 🆘 Support

If you encounter issues:
1.  Check the troubleshooting section above
2.  Review Docker logs: `docker-compose -f docker-compose.prod.yml logs`
3.  Check system resources: `htop`, `df -h`
4.  Verify network connectivity: `curl`, `ping`
5.  **Verify database connectivity and queries using `psql` from your droplet.**

Your GRO Early Learning ATS is now ready for production use with PostgreSQL! 