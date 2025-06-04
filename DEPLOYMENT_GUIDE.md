# 🚀 GRO Early Learning ATS - Digital Ocean Deployment Guide

Complete step-by-step guide to deploy your GRO Early Learning ATS on Digital Ocean.

## 📋 Prerequisites

- Digital Ocean account
- Domain name (optional but recommended)
- Basic command line knowledge

## 🖥️ Digital Ocean Droplet Setup

### Step 1: Create a Droplet

1. **Login to Digital Ocean**
   - Go to https://www.digitalocean.com/
   - Click "Create" → "Droplets"

2. **Configure Droplet**
   - **Image**: Ubuntu 22.04 LTS
   - **Plan**: 
     - Basic: $24/month (4GB RAM, 2 vCPUs, 80GB SSD) - Recommended
     - Or Premium: $48/month (8GB RAM, 2 vCPUs, 160GB SSD) - For high traffic
   - **Datacenter**: Choose closest to Queensland, Australia (Singapore recommended)
   - **Authentication**: 
     - Add your SSH key OR
     - Use password (less secure)
   - **Hostname**: `gro-ats-production`
   - **Backups**: Enable (recommended)
   - **Monitoring**: Enable

3. **Click "Create Droplet"**

### Step 2: Initial Server Setup

1. **Connect to your server**
   ```bash
   ssh root@your_droplet_ip
   ```

2. **Update system packages**
   ```bash
   apt update && apt upgrade -y
   ```

3. **Create a non-root user**
   ```bash
   adduser groats
   usermod -aG sudo groats
   ```

4. **Switch to new user**
   ```bash
   su - groats
   ```

## 🐳 Install Docker and Dependencies

### Step 3: Install Docker

```bash
# Install Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker groats
newgrp docker

# Verify installation
docker --version
docker-compose --version
```

### Step 4: Install Additional Tools

```bash
# Install essential tools
sudo apt install -y git curl wget unzip htop nginx-common certbot

# Install Node.js (for frontend build)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

## 📂 Deploy Application Code

### Step 5: Upload Application Files

**Option A: Using Git (Recommended)**
```bash
# Clone your repository (if you have the code in Git)
git clone https://github.com/your-username/gro-early-learning-ats.git
cd gro-early-learning-ats
```

**Option B: Using SCP to upload files**
```bash
# From your local machine, upload the entire app directory
scp -r /path/to/your/app groats@your_droplet_ip:/home/groats/gro-ats
```

**Option C: Manual file creation**
```bash
# Create project directory
mkdir -p /home/groats/gro-ats
cd /home/groats/gro-ats

# Create all the necessary files using the configurations provided
# (Copy the contents from the deployment files created earlier)
```

### Step 6: Configure Environment Variables

1. **Create production environment file**
   ```bash
   nano .env.production
   ```

2. **Add your production configuration**
   ```env
   # Database Configuration - USE MONGODB ATLAS FOR PRODUCTION
   MONGO_URL="mongodb+srv://username:password@your-cluster.mongodb.net"
   DB_NAME="gro_ats_production"
   
   # Local MongoDB (only if not using Atlas)
   MONGO_ROOT_USERNAME="groatsadmin"
   MONGO_ROOT_PASSWORD="your_secure_mongo_password"
   
   # SendGrid Email Configuration
   SENDGRID_API_KEY="SG.your_production_sendgrid_api_key"
   
   # Careers Site Integration
   CAREERS_SITE_URL="https://childcare-career-hub.lovable.app"
   CAREERS_WEBHOOK_SECRET="your_secure_webhook_secret_2025"
   
   # Security
   SECRET_KEY="your_very_long_secure_secret_key_for_jwt_tokens"
   
   # Application Settings
   ENVIRONMENT="production"
   DEBUG="false"
   LOG_LEVEL="INFO"
   ```

3. **Set proper permissions**
   ```bash
   chmod 600 .env.production
   ```

## 🗄️ Database Setup Options

### Option A: MongoDB Atlas (Recommended for Production)

1. **Create MongoDB Atlas Account**
   - Go to https://www.mongodb.com/atlas
   - Create free account
   - Create new cluster (M0 Sandbox is free)

2. **Configure Atlas**
   - Whitelist your Digital Ocean droplet IP
   - Create database user
   - Get connection string
   - Update `MONGO_URL` in `.env.production`

### Option B: Local MongoDB (Included in docker-compose)

- The `docker-compose.prod.yml` includes a MongoDB container
- Make sure to set strong passwords in environment variables
- Consider setting up regular backups

## 🚀 Deploy the Application

### Step 7: Build and Deploy

1. **Make deployment script executable**
   ```bash
   chmod +x deploy.sh backup.sh ssl-setup.sh
   ```

2. **Run deployment**
   ```bash
   ./deploy.sh
   ```

3. **Check deployment status**
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   docker-compose -f docker-compose.prod.yml logs
   ```

## 🔒 Configure SSL/HTTPS (Recommended)

### Step 8: Domain Configuration

1. **Point your domain to Digital Ocean**
   - In your domain registrar, update nameservers or A records
   - Point to your droplet's IP address
   - Wait for DNS propagation (up to 24 hours)

2. **Setup SSL certificate**
   ```bash
   ./ssl-setup.sh your-domain.com admin@yourdomain.com
   ```

## 🔥 Configure Firewall

### Step 9: Security Setup

```bash
# Enable UFW firewall
sudo ufw enable

# Allow SSH
sudo ufw allow 22

# Allow HTTP and HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Allow specific ports for development (optional)
sudo ufw allow 8001  # Backend API (optional, already proxied through nginx)

# Check firewall status
sudo ufw status
```

## 📊 Monitoring and Maintenance

### Step 10: Setup Monitoring

1. **Enable Docker stats monitoring**
   ```bash
   # Add this to crontab for regular monitoring
   echo "*/5 * * * * docker stats --no-stream >> /home/groats/gro-ats/logs/docker-stats.log" | crontab -
   ```

2. **Setup log rotation**
   ```bash
   sudo nano /etc/logrotate.d/gro-ats
   ```
   
   Add:
   ```
   /home/groats/gro-ats/logs/*.log {
       daily
       rotate 7
       compress
       delaycompress
       missingok
       notifempty
   }
   ```

3. **Setup automatic backups**
   ```bash
   # Add to crontab for daily backups at 2 AM
   echo "0 2 * * * /home/groats/gro-ats/backup.sh" | crontab -
   ```

## 🔧 Application Configuration

### Step 11: Configure Frontend Environment

1. **Update frontend environment**
   ```bash
   nano frontend/.env
   ```
   
   Update with your production domain:
   ```env
   REACT_APP_BACKEND_URL=https://your-domain.com
   ```

2. **Rebuild frontend** (if needed)
   ```bash
   docker-compose -f docker-compose.prod.yml build frontend
   docker-compose -f docker-compose.prod.yml up -d frontend
   ```

## 🧪 Testing Deployment

### Step 12: Verify Everything Works

1. **Test frontend access**
   ```bash
   curl -I https://your-domain.com
   ```

2. **Test backend API**
   ```bash
   curl https://your-domain.com/api/dashboard/stats
   ```

3. **Test webhook connection**
   ```bash
   curl -X POST https://your-domain.com/api/webhooks/test
   ```

4. **Check all services**
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   ```

## 📈 Performance Optimization

### Step 13: Optimize for Production

1. **Enable swap** (if needed for smaller droplets)
   ```bash
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```

2. **Configure Docker logging**
   ```bash
   # Add to docker daemon config
   sudo nano /etc/docker/daemon.json
   ```
   
   Add:
   ```json
   {
     "log-driver": "json-file",
     "log-opts": {
       "max-size": "10m",
       "max-file": "3"
     }
   }
   ```

## 🆘 Troubleshooting

### Common Issues and Solutions

1. **Port conflicts**
   ```bash
   sudo netstat -tulpn | grep :80
   sudo netstat -tulpn | grep :443
   ```

2. **Docker permission issues**
   ```bash
   sudo usermod -aG docker $USER
   newgrp docker
   ```

3. **Database connection issues**
   ```bash
   docker-compose -f docker-compose.prod.yml logs mongodb
   docker-compose -f docker-compose.prod.yml exec backend python -c "
   import asyncio
   from motor.motor_asyncio import AsyncIOMotorClient
   async def test(): 
       client = AsyncIOMotorClient('mongodb://localhost:27017')
       print(await client.admin.command('ismaster'))
   asyncio.run(test())
   "
   ```

4. **SSL certificate issues**
   ```bash
   sudo certbot certificates
   sudo certbot renew --dry-run
   ```

## 📋 Maintenance Commands

### Regular Maintenance

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Update application
git pull  # if using git
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Clean up Docker
docker system prune -f

# Monitor resource usage
htop
docker stats

# Backup data
./backup.sh

# Check webhook stats
curl https://your-domain.com/api/webhooks/stats
```

## 🎯 Final Checklist

- [ ] Droplet created and configured
- [ ] Docker and dependencies installed
- [ ] Application code deployed
- [ ] Environment variables configured
- [ ] Database setup (Atlas or local)
- [ ] SSL certificate installed
- [ ] Firewall configured
- [ ] Domain DNS configured
- [ ] Monitoring setup
- [ ] Backups configured
- [ ] Application tested and working
- [ ] Webhook integration tested

## 🔗 Useful URLs After Deployment

- **Frontend**: https://your-domain.com
- **Backend API**: https://your-domain.com/api
- **Health Check**: https://your-domain.com/health
- **API Documentation**: https://your-domain.com/api/docs (if enabled)
- **Webhook Stats**: https://your-domain.com/api/webhooks/stats

## 💰 Cost Estimation

**Monthly Costs:**
- Digital Ocean Droplet: $24-48/month
- Domain name: $10-15/year
- MongoDB Atlas (if used): $0-9/month
- SSL Certificate: Free (Let's Encrypt)
- **Total: ~$25-60/month**

## 🆘 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review Docker logs: `docker-compose -f docker-compose.prod.yml logs`
3. Check system resources: `htop`, `df -h`
4. Verify network connectivity: `curl`, `ping`

Your GRO Early Learning ATS is now ready for production use! 🎉