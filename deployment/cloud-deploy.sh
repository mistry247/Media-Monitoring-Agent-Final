#!/bin/bash

# Cloud Deployment Script for Media Monitoring Agent
# Supports AWS EC2, Google Cloud, DigitalOcean, and other cloud providers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="media-monitoring-agent"
REPO_URL="https://github.com/mistry247/media-monitoring-agent.git"
DOMAIN=""
EMAIL=""

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        log_error "Cannot detect OS"
        exit 1
    fi
    log_info "Detected OS: $OS $VER"
}

install_docker() {
    log_step "Installing Docker..."
    
    case "$OS" in
        *"Ubuntu"*|*"Debian"*)
            apt-get update
            apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
            echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
            apt-get update
            apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            ;;
        *"CentOS"*|*"Red Hat"*|*"Amazon Linux"*)
            yum update -y
            yum install -y yum-utils
            yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            systemctl start docker
            systemctl enable docker
            ;;
        *)
            log_error "Unsupported OS: $OS"
            exit 1
            ;;
    esac
    
    # Install docker-compose (standalone)
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    log_info "Docker installed successfully"
}

setup_firewall() {
    log_step "Configuring firewall..."
    
    if command -v ufw &> /dev/null; then
        # Ubuntu/Debian firewall
        ufw --force enable
        ufw allow ssh
        ufw allow 80/tcp
        ufw allow 443/tcp
        log_info "UFW firewall configured"
    elif command -v firewall-cmd &> /dev/null; then
        # CentOS/RHEL firewall
        systemctl start firewalld
        systemctl enable firewalld
        firewall-cmd --permanent --add-service=ssh
        firewall-cmd --permanent --add-service=http
        firewall-cmd --permanent --add-service=https
        firewall-cmd --reload
        log_info "Firewalld configured"
    else
        log_warn "No supported firewall found. Please configure manually."
    fi
}

clone_repository() {
    log_step "Cloning application repository..."
    
    cd /opt
    if [[ -d "$APP_NAME" ]]; then
        log_info "Repository already exists, pulling latest changes..."
        cd "$APP_NAME"
        git pull
    else
        git clone "$REPO_URL" "$APP_NAME"
        cd "$APP_NAME"
    fi
    
    log_info "Repository cloned/updated successfully"
}

setup_ssl() {
    if [[ -n "$DOMAIN" && -n "$EMAIL" ]]; then
        log_step "Setting up SSL with Let's Encrypt..."
        
        # Install certbot
        case "$OS" in
            *"Ubuntu"*|*"Debian"*)
                apt-get install -y certbot
                ;;
            *"CentOS"*|*"Red Hat"*|*"Amazon Linux"*)
                yum install -y certbot
                ;;
        esac
        
        # Generate SSL certificate
        certbot certonly --standalone -d "$DOMAIN" --email "$EMAIL" --agree-tos --non-interactive
        
        # Create SSL directory and copy certificates
        mkdir -p ssl
        cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ssl/
        cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" ssl/
        
        # Set up auto-renewal
        echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
        
        log_info "SSL certificate configured for $DOMAIN"
    else
        log_warn "Domain and email not provided, skipping SSL setup"
    fi
}

configure_environment() {
    log_step "Configuring environment..."
    
    if [[ ! -f ".env" ]]; then
        if [[ -f "deployment/production.env" ]]; then
            cp "deployment/production.env" ".env"
            log_warn "Created .env from production template. Please edit with your settings:"
            log_warn "  - CLAUDE_API_KEY: Your Google Gemini API key"
            log_warn "  - SMTP settings: Your email configuration"
            log_warn "  - EMAIL_RECIPIENTS: Your recipient list"
            log_warn "  - CORS_ORIGINS: Your domain"
            echo
            read -p "Press Enter after editing .env file..."
        else
            log_error "No environment template found"
            exit 1
        fi
    fi
    
    # Create necessary directories
    mkdir -p data logs ssl
    chmod 755 data logs
}

deploy_application() {
    log_step "Deploying application with Docker..."
    
    # Build and start the application
    docker-compose down 2>/dev/null || true
    docker-compose up -d --build
    
    # Wait for application to start
    log_info "Waiting for application to start..."
    sleep 30
    
    # Check if application is running
    if docker-compose ps | grep -q "Up"; then
        log_info "Application deployed successfully!"
    else
        log_error "Application failed to start. Check logs:"
        docker-compose logs
        exit 1
    fi
}

setup_monitoring() {
    log_step "Setting up monitoring and backups..."
    
    # Set up log rotation
    cat > /etc/logrotate.d/media-monitoring << EOF
/opt/$APP_NAME/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
}
EOF
    
    # Set up backup script
    chmod +x deployment/backup.sh
    
    # Add backup cron job (daily at 2 AM)
    echo "0 2 * * * /opt/$APP_NAME/deployment/backup.sh" | crontab -
    
    log_info "Monitoring and backups configured"
}

show_completion_info() {
    log_info "Deployment completed successfully!"
    echo
    echo "=== Deployment Summary ==="
    echo "Application URL: http://$(curl -s ifconfig.me):8000"
    if [[ -n "$DOMAIN" ]]; then
        echo "Domain URL: https://$DOMAIN"
    fi
    echo "Application directory: /opt/$APP_NAME"
    echo
    echo "=== Management Commands ==="
    echo "View logs: docker-compose -f /opt/$APP_NAME/docker-compose.yml logs -f"
    echo "Restart app: docker-compose -f /opt/$APP_NAME/docker-compose.yml restart"
    echo "Stop app: docker-compose -f /opt/$APP_NAME/docker-compose.yml down"
    echo "Update app: cd /opt/$APP_NAME && git pull && docker-compose up -d --build"
    echo
    echo "=== Next Steps ==="
    echo "1. Test the application by visiting the URL above"
    echo "2. Submit a test article to verify functionality"
    echo "3. Check email delivery is working"
    echo "4. Set up monitoring alerts if needed"
    echo
}

# Main deployment function
main() {
    log_info "Starting cloud deployment of Media Monitoring Agent..."
    
    # Get user input
    read -p "Enter your domain name (optional, press Enter to skip): " DOMAIN
    if [[ -n "$DOMAIN" ]]; then
        read -p "Enter your email for SSL certificate: " EMAIL
    fi
    
    check_root
    detect_os
    
    # Install dependencies
    if ! command -v docker &> /dev/null; then
        install_docker
    else
        log_info "Docker already installed"
    fi
    
    setup_firewall
    clone_repository
    configure_environment
    
    if [[ -n "$DOMAIN" ]]; then
        setup_ssl
    fi
    
    deploy_application
    setup_monitoring
    show_completion_info
}

# Usage information
usage() {
    echo "Usage: $0"
    echo ""
    echo "This script will:"
    echo "1. Install Docker and dependencies"
    echo "2. Configure firewall"
    echo "3. Clone the application repository"
    echo "4. Set up SSL (if domain provided)"
    echo "5. Deploy the application"
    echo "6. Configure monitoring and backups"
    echo ""
    echo "Requirements:"
    echo "- Fresh Ubuntu/Debian/CentOS server"
    echo "- Root access"
    echo "- Internet connection"
    echo ""
}

# Check for help flag
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

# Run main deployment
main