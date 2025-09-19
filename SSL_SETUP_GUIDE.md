# 🔐 SSL Setup Guide for Media Monitoring Agent

## The Problem
Your HTTPS (https://media-monitor.link/) stopped working in v3.0 because the SSL configuration was missing from the nginx setup.

## The Solution
I've fixed the configuration files. Here's what you need to do:

### Step 1: Update Your Server
1. **SSH into your server**:
   ```bash
   ssh root@167.99.200.184
   ```

2. **Pull the latest changes**:
   ```bash
   cd /opt/media-monitoring-agent  # or wherever your app is located
   git pull origin main
   ```

### Step 2: Set Up SSL Certificates
1. **Edit the SSL setup script** with your email:
   ```bash
   nano setup-ssl.sh
   ```
   Change `EMAIL="your-email@example.com"` to your actual email address.

2. **Run the SSL setup script**:
   ```bash
   sudo ./setup-ssl.sh
   ```

### Step 3: Verify Everything Works
1. **Check if the containers are running**:
   ```bash
   docker-compose ps
   ```

2. **Test HTTPS access**:
   - Visit: https://media-monitor.link/
   - Should redirect from HTTP to HTTPS automatically

## What I Fixed

### 1. Updated `deployment/nginx.conf`
- ✅ Added HTTPS server block (port 443)
- ✅ Added HTTP to HTTPS redirect
- ✅ Added SSL certificate configuration
- ✅ Added security headers

### 2. Updated `docker-compose.yml`
- ✅ Added port 443 exposure
- ✅ Added SSL certificate volume mounts

### 3. Created `setup-ssl.sh`
- ✅ Automated SSL certificate generation
- ✅ Automatic certificate renewal setup
- ✅ Proper file permissions

## Troubleshooting

### If SSL setup fails:
1. **Make sure your domain points to your server**:
   ```bash
   nslookup media-monitor.link
   ```

2. **Check if ports 80 and 443 are open**:
   ```bash
   ufw status
   # Should show:
   # 80/tcp                     ALLOW       Anywhere
   # 443/tcp                    ALLOW       Anywhere
   ```

3. **Check nginx logs**:
   ```bash
   docker-compose logs nginx
   ```

### If you get SSL errors:
- Wait 5-10 minutes for DNS propagation
- Clear your browser cache
- Try incognito/private browsing mode

## Why This Happened in v3.0

The issue occurred because v3.0 focused on application features but the SSL configuration got simplified during the Docker transition. The nginx configuration was reduced to HTTP-only, removing the HTTPS setup that was working in v2.0.

## Alternative: Quick Manual SSL Setup

If the script doesn't work, you can manually set up SSL:

```bash
# Install certbot
apt-get install -y certbot

# Stop the application
docker-compose down

# Generate certificate
certbot certonly --standalone -d media-monitor.link

# Copy certificates
mkdir -p deployment/ssl
cp /etc/letsencrypt/live/media-monitor.link/fullchain.pem deployment/ssl/
cp /etc/letsencrypt/live/media-monitor.link/privkey.pem deployment/ssl/

# Start the application
docker-compose up -d
```

## Should You Revert to v2.0?

**No, don't revert!** The fixes I've provided will restore HTTPS functionality while keeping all the v3.0 improvements. The issue was just a missing configuration, not a fundamental problem with v3.0.

---

**Need help?** Run the SSL setup script and your HTTPS should be working again! 🚀
