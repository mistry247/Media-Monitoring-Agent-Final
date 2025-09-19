#!/bin/bash

# SSL Setup Script for Media Monitoring Agent
# This script sets up Let's Encrypt SSL certificates for media-monitor.link

set -e

DOMAIN="media-monitor.link"
EMAIL="your-email@example.com"  # Change this to your email

echo "🔐 Setting up SSL certificates for $DOMAIN"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)"
   exit 1
fi

# Install certbot if not already installed
if ! command -v certbot &> /dev/null; then
    echo "📦 Installing certbot..."
    apt-get update
    apt-get install -y certbot
fi

# Create deployment/ssl directory
mkdir -p deployment/ssl

# Stop nginx temporarily for certificate generation
echo "⏸️  Stopping nginx temporarily..."
docker-compose down || true

# Generate SSL certificate using standalone mode
echo "🔑 Generating SSL certificate..."
certbot certonly --standalone \
    -d "$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --non-interactive \
    --force-renewal

# Copy certificates to deployment/ssl directory
echo "📋 Copying certificates..."
cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" deployment/ssl/
cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" deployment/ssl/

# Set proper permissions
chmod 644 deployment/ssl/fullchain.pem
chmod 600 deployment/ssl/privkey.pem

# Set up auto-renewal
echo "🔄 Setting up auto-renewal..."
cat > /etc/cron.d/certbot-renewal << EOF
# Renew Let's Encrypt certificates twice daily
0 */12 * * * root /usr/bin/certbot renew --quiet --deploy-hook "cd /opt/media-monitoring-agent && cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem deployment/ssl/ && cp /etc/letsencrypt/live/$DOMAIN/privkey.pem deployment/ssl/ && docker-compose restart nginx"
EOF

echo "✅ SSL setup complete!"
echo ""
echo "🚀 Starting application with SSL..."
docker-compose up -d

echo ""
echo "🎉 Your application is now available at:"
echo "   https://$DOMAIN"
echo ""
echo "📝 Note: It may take a few minutes for the SSL to propagate."
echo "   If you get SSL errors, wait 5-10 minutes and try again."
