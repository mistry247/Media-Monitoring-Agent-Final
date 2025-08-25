#!/bin/bash

# Media Monitoring Agent Deployment Script
# This script helps deploy the application in various environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="media-monitoring-agent"
APP_USER="www-data"
APP_DIR="/opt/$APP_NAME"
SERVICE_NAME="media-monitoring"

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

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

install_dependencies() {
    log_info "Installing system dependencies..."
    apt-get update
    apt-get install -y python3 python3-pip python3-venv git curl nginx
}

create_user() {
    if ! id "$APP_USER" &>/dev/null; then
        log_info "Creating application user: $APP_USER"
        useradd -r -s /bin/false -d "$APP_DIR" "$APP_USER"
    else
        log_info "User $APP_USER already exists"
    fi
}

setup_application() {
    log_info "Setting up application directory..."
    
    # Create directories
    mkdir -p "$APP_DIR"/{data,logs}
    
    # Copy application files (assuming script is run from project root)
    cp -r . "$APP_DIR/"
    
    # Set up Python virtual environment
    log_info "Creating Python virtual environment..."
    python3 -m venv "$APP_DIR/venv"
    
    # Install Python dependencies
    log_info "Installing Python dependencies..."
    "$APP_DIR/venv/bin/pip" install --upgrade pip
    "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"
    
    # Set permissions
    chown -R "$APP_USER:$APP_USER" "$APP_DIR"
    chmod +x "$APP_DIR/migrate.py"
    chmod +x "$APP_DIR/deployment/backup.sh"
}

setup_environment() {
    log_info "Setting up environment configuration..."
    
    if [[ ! -f "$APP_DIR/.env" ]]; then
        if [[ -f "$APP_DIR/.env.example" ]]; then
            cp "$APP_DIR/.env.example" "$APP_DIR/.env"
            log_warn "Created .env file from .env.example. Please edit $APP_DIR/.env with your configuration."
        else
            log_error ".env.example file not found. Please create $APP_DIR/.env manually."
            exit 1
        fi
    else
        log_info ".env file already exists"
    fi
}

setup_database() {
    log_info "Setting up database..."
    
    # Run migrations as the app user
    sudo -u "$APP_USER" "$APP_DIR/venv/bin/python" "$APP_DIR/migrate.py" migrate
}

setup_systemd() {
    log_info "Setting up systemd service..."
    
    # Copy service file
    cp "$APP_DIR/deployment/media-monitoring.service" "/etc/systemd/system/"
    
    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
}

setup_nginx() {
    log_info "Setting up nginx configuration..."
    
    # Backup existing nginx config if it exists
    if [[ -f "/etc/nginx/nginx.conf" ]]; then
        cp "/etc/nginx/nginx.conf" "/etc/nginx/nginx.conf.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # Copy nginx configuration
    cp "$APP_DIR/deployment/nginx.conf" "/etc/nginx/"
    
    # Test nginx configuration
    nginx -t
    
    log_warn "Nginx configuration updated. You may need to configure SSL certificates."
    log_warn "Update the SSL certificate paths in /etc/nginx/nginx.conf"
}

start_services() {
    log_info "Starting services..."
    
    # Start and enable the application service
    systemctl start "$SERVICE_NAME"
    systemctl status "$SERVICE_NAME" --no-pager
    
    # Restart nginx
    systemctl restart nginx
    systemctl enable nginx
}

# Main deployment function
deploy_systemd() {
    log_info "Starting systemd deployment..."
    
    check_root
    install_dependencies
    create_user
    setup_application
    setup_environment
    setup_database
    setup_systemd
    
    # Ask about nginx setup
    read -p "Do you want to set up nginx reverse proxy? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        setup_nginx
    fi
    
    start_services
    
    log_info "Deployment completed successfully!"
    log_info "Application should be running on http://localhost:8000"
    log_info "Check status with: systemctl status $SERVICE_NAME"
    log_info "View logs with: journalctl -u $SERVICE_NAME -f"
}

# Docker deployment
deploy_docker() {
    log_info "Starting Docker deployment..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Create necessary directories
    mkdir -p data logs
    
    # Check for .env file
    if [[ ! -f ".env" ]]; then
        if [[ -f ".env.example" ]]; then
            cp ".env.example" ".env"
            log_warn "Created .env file from .env.example. Please edit .env with your configuration."
            read -p "Press Enter to continue after editing .env file..."
        else
            log_error ".env.example file not found. Please create .env file manually."
            exit 1
        fi
    fi
    
    # Build and start containers
    log_info "Building and starting Docker containers..."
    docker-compose up -d --build
    
    # Show status
    docker-compose ps
    
    log_info "Docker deployment completed!"
    log_info "Application should be running on http://localhost:8000"
    log_info "Check logs with: docker-compose logs -f"
}

# Usage information
usage() {
    echo "Usage: $0 [systemd|docker]"
    echo ""
    echo "Deployment options:"
    echo "  systemd    Deploy using systemd service (Linux)"
    echo "  docker     Deploy using Docker containers"
    echo ""
    echo "Examples:"
    echo "  $0 systemd    # Deploy with systemd (requires root)"
    echo "  $0 docker     # Deploy with Docker"
}

# Main script logic
case "${1:-}" in
    "systemd")
        deploy_systemd
        ;;
    "docker")
        deploy_docker
        ;;
    *)
        usage
        exit 1
        ;;
esac