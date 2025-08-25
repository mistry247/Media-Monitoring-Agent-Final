# Media Monitoring Agent - Cloud Deployment Guide

This guide will help you deploy the Media Monitoring Agent to a cloud server (AWS EC2, Google Cloud, DigitalOcean, etc.).

## 🚀 Quick Start

### Option 1: Automated Cloud Deployment (Recommended)

1. **Prepare your cloud server:**
   - Ubuntu 20.04+ or CentOS 8+ 
   - Minimum 2GB RAM, 20GB disk
   - Public IP address
   - SSH access as root

2. **Run the automated deployment:**
   ```bash
   # On your cloud server
   curl -fsSL https://raw.githubusercontent.com/mistry247/media-monitoring-agent/main/deployment/cloud-deploy.sh | bash
   ```

3. **Follow the prompts:**
   - Enter your domain name (optional, for SSL)
   - Enter your email (for SSL certificates)
   - Wait for deployment to complete

### Option 2: Manual Docker Deployment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mistry247/media-monitoring-agent.git
   cd media-monitoring-agent
   ```

2. **Install Docker:**
   ```bash
   # Ubuntu/Debian
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER
   
   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

3. **Configure environment:**
   ```bash
   cp deployment/production.env .env
   nano .env  # Edit with your settings
   ```

4. **Deploy:**
   ```bash
   docker-compose up -d --build
   ```

## ⚙️ Configuration

### Required Environment Variables

Edit your `.env` file with these essential settings:

```bash
# Google Gemini API (Get from Google AI Studio)
CLAUDE_API_KEY=your_gemini_api_key_here

# Email Configuration (Gmail example)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password  # Use App Password, not regular password
EMAIL_FROM=your_email@gmail.com
EMAIL_RECIPIENTS=recipient1@company.com,recipient2@company.com

# Domain (if using SSL)
CORS_ORIGINS=https://yourdomain.com
```

### Getting API Keys

1. **Google Gemini API Key:**
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Copy the key to your `.env` file

2. **Gmail App Password:**
   - Enable 2-factor authentication on your Gmail account
   - Go to Google Account settings > Security > App passwords
   - Generate an app password for "Mail"
   - Use this password in your `.env` file

## 🌐 Cloud Provider Setup

### AWS EC2

1. **Launch EC2 instance:**
   - AMI: Ubuntu 20.04 LTS
   - Instance type: t3.small or larger
   - Security group: Allow ports 22, 80, 443

2. **Connect and deploy:**
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-ip
   sudo su -
   curl -fsSL https://raw.githubusercontent.com/mistry247/media-monitoring-agent/main/deployment/cloud-deploy.sh | bash
   ```

### Google Cloud Platform

1. **Create VM instance:**
   ```bash
   gcloud compute instances create media-monitoring \
     --image-family=ubuntu-2004-lts \
     --image-project=ubuntu-os-cloud \
     --machine-type=e2-small \
     --tags=http-server,https-server
   ```

2. **Deploy:**
   ```bash
   gcloud compute ssh media-monitoring
   sudo su -
   curl -fsSL https://raw.githubusercontent.com/mistry247/media-monitoring-agent/main/deployment/cloud-deploy.sh | bash
   ```

### DigitalOcean

1. **Create droplet:**
   - Ubuntu 20.04
   - Basic plan: $12/month (2GB RAM)
   - Add your SSH key

2. **Deploy:**
   ```bash
   ssh root@your-droplet-ip
   curl -fsSL https://raw.githubusercontent.com/mistry247/media-monitoring-agent/main/deployment/cloud-deploy.sh | bash
   ```

## 🔒 Security Setup

### SSL Certificate (Let's Encrypt)

If you provided a domain during deployment, SSL is automatically configured. Otherwise:

```bash
# Install certbot
sudo apt install certbot

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Copy certificates
sudo mkdir -p /opt/media-monitoring-agent/ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /opt/media-monitoring-agent/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem /opt/media-monitoring-agent/ssl/

# Restart application
cd /opt/media-monitoring-agent
docker-compose restart
```

### Firewall Configuration

```bash
# Ubuntu/Debian (UFW)
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## 📊 Monitoring & Maintenance

### Check Application Status

```bash
# View running containers
docker-compose ps

# View logs
docker-compose logs -f

# Check health
curl http://localhost:8000/health
```

### Backup & Updates

```bash
# Manual backup
cd /opt/media-monitoring-agent
./deployment/backup.sh

# Update application
git pull
docker-compose up -d --build
```

### Log Management

Logs are automatically rotated daily and kept for 30 days. View logs:

```bash
# Application logs
tail -f /opt/media-monitoring-agent/logs/media_monitoring.log

# Docker logs
docker-compose logs -f media-monitoring
```

## 🧪 Testing Your Deployment

1. **Access the web interface:**
   - Open `http://your-server-ip:8000` in your browser
   - Or `https://yourdomain.com` if you configured SSL

2. **Submit a test article:**
   - Use the web form to submit a news article URL
   - Check that it processes successfully

3. **Verify email delivery:**
   - Generate a test report
   - Confirm emails are received

4. **Check API endpoints:**
   ```bash
   # Health check
   curl http://your-server-ip:8000/health
   
   # Submit article via API
   curl -X POST http://your-server-ip:8000/api/articles/submit \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com/news-article", "submitted_by": "test"}'
   ```

## 🆘 Troubleshooting

### Common Issues

1. **Application won't start:**
   ```bash
   # Check logs
   docker-compose logs media-monitoring
   
   # Verify .env file
   cat .env
   ```

2. **Email not working:**
   - Verify SMTP settings in `.env`
   - Check Gmail app password is correct
   - Ensure 2FA is enabled on Gmail

3. **API errors:**
   - Verify Gemini API key is valid
   - Check network connectivity
   - Review application logs

4. **SSL issues:**
   ```bash
   # Renew certificate
   sudo certbot renew
   
   # Check certificate status
   sudo certbot certificates
   ```

### Getting Help

- Check logs: `docker-compose logs -f`
- Verify configuration: Review `.env` file
- Test connectivity: `curl http://localhost:8000/health`
- Check firewall: Ensure ports 80/443 are open

## 📋 Production Checklist

Use the comprehensive checklist in `deployment/PRODUCTION_CHECKLIST.md` to ensure your deployment is production-ready.

## 🔄 Scaling & Performance

For high-traffic deployments:

1. **Use a load balancer** (AWS ALB, Nginx, etc.)
2. **Scale horizontally** with multiple containers
3. **Use external database** (PostgreSQL, MySQL)
4. **Implement caching** (Redis)
5. **Monitor performance** (Prometheus, Grafana)

---

**Need help?** Check the troubleshooting section or review the logs for specific error messages.