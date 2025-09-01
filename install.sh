#!/bin/bash

# Media Monitoring Agent - Clean Installation Script
# This script performs a complete fresh installation on a new server

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root (use sudo)"
    exit 1
fi

log_info "🚀 Starting Media Monitoring Agent installation..."

# Detect OS
if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    OS=$NAME
    log_info "Detected OS: $OS"
else
    log_error "Cannot detect OS"
    exit 1
fi

log_step "Step 1: Installing Docker..."
case "$OS" in
    *"Ubuntu"*|*"Debian"*)
        apt-get update
        apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release git
        
        # Add Docker's official GPG key
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        
        # Add Docker repository
        echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
        
        # Install Docker
        apt-get update
        apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
        ;;
    *"CentOS"*|*"Red Hat"*|*"Amazon Linux"*)
        yum update -y
        yum install -y yum-utils git
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

log_info "✓ Docker installed successfully"

log_step "Step 2: Configuring firewall..."
if command -v ufw &> /dev/null; then
    ufw --force enable
    ufw allow ssh
    ufw allow 80/tcp
    log_info "✓ UFW firewall configured"
elif command -v firewall-cmd &> /dev/null; then
    systemctl start firewalld
    systemctl enable firewalld
    firewall-cmd --permanent --add-service=ssh
    firewall-cmd --permanent --add-service=http
    firewall-cmd --reload
    log_info "✓ Firewalld configured"
else
    log_warn "No supported firewall found"
fi

log_step "Step 3: Cloning application repository..."
cd /opt
REPO_URL="https://github.com/YOUR-USERNAME/media-monitoring-agent-clean.git"
APP_NAME="media-monitoring-agent"

if [[ -d "$APP_NAME" ]]; then
    log_warn "Directory already exists, removing..."
    rm -rf "$APP_NAME"
fi

git clone "$REPO_URL" "$APP_NAME"
cd "$APP_NAME"

log_info "✓ Repository cloned successfully"

log_step "Step 4: Creating environment configuration..."
if [[ ! -f ".env" ]]; then
    cp .env.example .env
    log_info "✓ Created .env file from template"
else
    log_info "✓ .env file already exists"
fi

log_step "Step 5: Configuration required..."
echo ""
echo "=================================================="
echo "🔧 CONFIGURATION REQUIRED"
echo "=================================================="
echo ""
echo "Please edit the .env file with your settings:"
echo ""
echo "Required settings:"
echo "  - CLAUDE_API_KEY: Your Google Gemini API key"
echo "  - EMAIL_RECIPIENTS: Your email addresses"
echo ""
echo "Get your Gemini API key from:"
echo "  https://aistudio.google.com/app/apikey"
echo ""
echo "The .env file is located at: /opt/$APP_NAME/.env"
echo ""
echo "You can edit it with: nano .env"
echo ""
echo "=================================================="
echo ""

read -p "Press Enter after you have edited the .env file..."

log_step "Step 6: Creating necessary directories..."
mkdir -p data logs
chmod 755 data logs

log_step "Step 7: Starting the application..."
log_info "Building and starting containers (this may take a few minutes)..."

docker-compose up -d --build

log_step "Step 8: Waiting for application to start..."
sleep 30

log_step "Step 9: Checking application status..."
if docker-compose ps | grep -q "Up"; then
    log_info "✓ Application containers are running"
else
    log_error "✗ Some containers failed to start"
    docker-compose logs
    exit 1
fi

# Test application health
log_step "Step 10: Testing application health..."
sleep 10

if curl -f http://localhost/health > /dev/null 2>&1; then
    log_info "✓ Application is responding to health checks"
else
    log_warn "⚠ Application may still be starting up"
fi

# Get server IP
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s icanhazip.com 2>/dev/null || echo "YOUR-SERVER-IP")

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "=================================================="
echo "📋 DEPLOYMENT SUMMARY"
echo "=================================================="
echo ""
echo "Application URL: http://$SERVER_IP"
echo "Application directory: /opt/$APP_NAME"
echo ""
echo "=================================================="
echo "🔧 MANAGEMENT COMMANDS"
echo "=================================================="
echo ""
echo "View logs:     docker-compose -f /opt/$APP_NAME/docker-compose.yml logs -f"
echo "Restart app:   docker-compose -f /opt/$APP_NAME/docker-compose.yml restart"
echo "Stop app:      docker-compose -f /opt/$APP_NAME/docker-compose.yml down"
echo "Update app:    cd /opt/$APP_NAME && git pull && docker-compose up -d --build"
echo ""
echo "=================================================="
echo "✅ NEXT STEPS"
echo "=================================================="
echo ""
echo "1. Visit http://$SERVER_IP to access the web interface"
echo "2. Submit a test article to verify functionality"
echo "3. Generate a test report to verify email delivery"
echo "4. Check that emails are received at your configured addresses"
echo ""
echo "=================================================="
echo "🆘 TROUBLESHOOTING"
echo "=================================================="
echo ""
echo "Check container status: docker-compose ps"
echo "View application logs:  docker-compose logs media-monitoring"
echo "Test health endpoint:   curl http://localhost/health"
echo "Check configuration:    cat .env"
echo ""
echo "Installation complete! 🚀"
echo ""