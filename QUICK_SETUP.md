# 🚀 GRO Early Learning ATS - Quick Setup for ats.regionalchildcare.com

## Pre-configured for your domain!
This deployment is specifically configured for: **ats.regionalchildcare.com**

## 🎯 Quick Deployment Steps

### 1. Create Digital Ocean Droplet
- **Image**: Ubuntu 22.04 LTS
- **Size**: $24/month (4GB RAM, 2 vCPUs)
- **Datacenter**: Singapore (closest to Queensland)
- **Hostname**: `regionalchildcare-ats`

### 2. Upload Files to Server
```bash
# From your local machine
scp -r /path/to/gro-ats root@your_droplet_ip:/home/
```

### 3. Configure Your Credentials
```bash
# SSH into your server
ssh root@your_droplet_ip

# Edit production environment
cd /home/gro-ats
nano .env.production
```

**Required Changes in .env.production:**
```env
# Update these with your actual credentials:
MONGO_URL="mongodb+srv://username:password@your-cluster.mongodb.net"
SENDGRID_API_KEY="SG.your_actual_sendgrid_key_here"

# Keep these (already configured for your domain):
DOMAIN="ats.regionalchildcare.com"
CAREERS_SITE_URL="https://childcare-career-hub.lovable.app"
CAREERS_WEBHOOK_SECRET="gro-regionalchildcare-webhook-2025"
SECRET_KEY="ats-regionalchildcare-secure-secret-key-2025"
```

### 4. Deploy Everything
```bash
# Install Docker and dependencies (one-time setup)
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Deploy the application
./deploy.sh
```

### 5. Configure DNS
**In your domain registrar (where you manage regionalchildcare.com):**
- Create A record: `ats` pointing to your droplet IP
- Wait for DNS propagation (up to 24 hours)

### 6. Setup SSL Certificate
```bash
# Once DNS is pointing to your server
./ssl-setup.sh
```

## 🎉 You're Done!

Your GRO Early Learning ATS will be live at:
- **🌐 Frontend**: https://ats.regionalchildcare.com
- **🔧 API**: https://ats.regionalchildcare.com/api
- **📊 Webhook Stats**: https://ats.regionalchildcare.com/api/webhooks/stats

## 🔧 Management Commands

```bash
# Check health
./health-check.sh

# Create backup
./backup.sh

# Update application
./update.sh

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

## 📞 Support

If you encounter issues:
1. Check the main DEPLOYMENT_GUIDE.md for detailed troubleshooting
2. Run `./health-check.sh` to diagnose problems
3. Check logs: `docker-compose -f docker-compose.prod.yml logs`

## 🔗 Integration Status

✅ **Careers Site Integration**: Pre-configured for childcare-career-hub.lovable.app  
✅ **Domain Configuration**: Set for ats.regionalchildcare.com  
✅ **Webhook Security**: Configured with secure secret key  
✅ **SSL Ready**: Auto-setup with Let's Encrypt  

Your ATS is ready to manage recruitment for regional Queensland childcare centers! 🌟